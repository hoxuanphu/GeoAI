"""Bounded ZIP inspection from immutable bytes, with no extraction or registration.

Only STORE and raw DEFLATE are supported. All names/metadata are checked before
content; actual output is bounded and hashed without trusting uncompressed sizes.
Known content signatures are exclusion checks, never a claim of parser safety.
"""
from collections.abc import Callable, Iterator
from datetime import datetime
import hashlib
import io
import re
import stat
import struct
import time
import unicodedata
import zipfile
import zlib

from geoai.contracts.imports import ArchiveEntry, ArchiveInventory, ArchivePolicy

_FORBIDDEN_EXTENSIONS = frozenset((
    ".zip", ".7z", ".rar", ".gz", ".bz2", ".xz", ".tar", ".tgz", ".jar",
    ".vrt", ".exe", ".dll", ".so", ".dylib", ".com", ".scr", ".msi",
    ".bat", ".cmd", ".ps1", ".vbs", ".js", ".py", ".pyc", ".pyo",
    ".pkl", ".pickle", ".joblib", ".pt", ".pth", ".ckpt", ".onnx", ".safetensors",
))
_RESERVED = frozenset(("con", "prn", "aux", "nul", "conin$", "conout$", *(
    f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)
)))
_EXTRA_ALLOWLIST = frozenset((0x5455, 0x7875))  # timestamp and UID/GID only; ZIP64 unsupported


class ImportRejected(ValueError):
    """Stable sanitized failure; never attach hostile paths or nested exceptions."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _name(value: str, max_depth: int) -> tuple[str, bool]:
    # Compatibility normalization also catches fullwidth separators/device names.
    normalized = unicodedata.normalize("NFKC", value).replace("\\", "/")
    directory = normalized.endswith("/")
    path = normalized[:-1] if directory else normalized
    parts = path.split("/")
    if not path:
        raise ImportRejected("invalid_path")
    for part in parts:
        stem = part.split(".", 1)[0].rstrip(" .").casefold()
        if (part in ("", ".", "..") or part[-1:] in (".", " ") or stem in _RESERVED
                or any(char in '<>:"|?*' or unicodedata.category(char).startswith("C") for char in part)):
            raise ImportRejected("invalid_path")
    if len(parts) > max_depth:
        raise ImportRejected("resource_exhausted")
    return "/".join(parts), directory


def _zip_envelope(source: bytes, policy: ArchivePolicy) -> tuple[int, int]:
    """Refuse stdlib's permissive prefix/trailing/multivolume ZIP compatibility.

    Only the fixed classic EOCD envelope is inspected here; ZipFile remains the
    central-directory/name/overlap parser. All local bytes must belong to members.
    """
    end = source.rfind(b"PK\x05\x06", max(0, len(source) - 65557))
    if end < 0 or len(source) - end < 22:
        raise ImportRejected("invalid_archive")
    _, disk, central_disk, disk_count, count, central_size, central_start, comment_size = struct.unpack_from(
        "<4s4H2IH", source, end)
    if disk or central_disk or count == 0xffff or central_size == 0xffffffff or central_start == 0xffffffff:
        raise ImportRejected("unsupported_archive")
    if (end + 22 + comment_size != len(source) or disk_count != count
            or central_start + central_size != end):
        raise ImportRejected("invalid_archive")
    if count > policy.max_entries:
        raise ImportRejected("resource_exhausted")
    return central_start, count


def _member_coverage(source: bytes, infos: list[zipfile.ZipInfo], central_start: int,
                     check: Callable[[], None]) -> None:
    position = 0
    for info in sorted(infos, key=lambda item: item.header_offset):
        check()
        if info.header_offset != position:
            raise ImportRejected("invalid_archive")
        header = struct.unpack_from("<4s5H3I2H", source, position)
        if header[0] != b"PK\x03\x04":
            raise ImportRejected("invalid_archive")
        position += 30 + header[-2] + header[-1] + info.compress_size
        if position > central_start:
            raise ImportRejected("invalid_archive")
    if position != central_start:
        raise ImportRejected("invalid_archive")


def _extra_fields(extra: bytes) -> None:
    position = 0
    while position < len(extra):
        if len(extra) - position < 4:
            raise ImportRejected("unsupported_metadata")
        tag, size = struct.unpack_from("<HH", extra, position)
        position += 4
        if tag not in _EXTRA_ALLOWLIST or position + size > len(extra):
            raise ImportRejected("unsupported_metadata")
        position += size


def _metadata(info: zipfile.ZipInfo, directory: bool) -> None:
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if (kind not in (0, stat.S_IFREG, stat.S_IFDIR) or info.external_attr & 0x400
            or (kind == stat.S_IFDIR and not directory)
            or (kind == stat.S_IFREG and directory)
            or (info.external_attr & 0x10 and not directory)):
        raise ImportRejected("unsupported_metadata")
    _extra_fields(info.extra)
    if info.flag_bits & ~0x806:  # UTF8 and DEFLATE options only; descriptors/encryption denied
        raise ImportRejected("unsupported_archive")
    if info.volume or info.extract_version > 20 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ImportRejected("unsupported_archive")


def _content_exclusions(prefix: bytes) -> None:
    signatures = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08", b"\x1f\x8b", b"BZh",
                  b"\xfd7zXZ\x00", b"7z\xbc\xaf\x27\x1c", b"Rar!", b"MZ", b"\x7fELF",
                  b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce")
    if (prefix.startswith(signatures) or prefix[257:262] == b"ustar"
            or (len(prefix) >= 2 and prefix[0] == 0x80 and prefix[1] <= 5)
            or re.search(br"<\s*vrtdataset\b", prefix, re.IGNORECASE)):
        raise ImportRejected("unsupported_content")


def _chunks(source: bytes, offset: int, compressed_size: int, method: int,
            chunk_bytes: int, check: Callable[[], None]) -> Iterator[bytes]:
    end = offset + compressed_size
    if offset < 0 or end > len(source):
        raise ImportRejected("invalid_archive")
    if method == zipfile.ZIP_STORED:
        for position in range(offset, end, chunk_bytes):
            check()
            yield source[position:min(position + chunk_bytes, end)]
        return
    decoder = zlib.decompressobj(-zlib.MAX_WBITS)
    for position in range(offset, end, chunk_bytes):
        pending = source[position:min(position + chunk_bytes, end)]
        while pending:
            check()
            expanded = decoder.decompress(pending, chunk_bytes)
            pending = decoder.unconsumed_tail
            if decoder.unused_data:
                raise ImportRejected("invalid_archive")
            if expanded:
                yield expanded
    # max_length can leave buffered output after all input has been consumed.
    while not decoder.eof:
        check()
        expanded = decoder.decompress(b"", chunk_bytes)
        if not expanded:
            raise ImportRejected("invalid_archive")
        yield expanded
    if decoder.unused_data or decoder.unconsumed_tail:
        raise ImportRejected("invalid_archive")


def inspect_zip(source: bytes, policy: ArchivePolicy, *, inventory_id: str,
                created_at: datetime, cancelled: Callable[[], bool] = lambda: False,
                monotonic: Callable[[], float] = time.monotonic) -> ArchiveInventory:
    """Inspect bytes under trusted policy; return only after every entry passes.

    Cancellation/deadlines are cooperative between bounded chunks. Callers must
    supply a trusted monotonic clock and must not accept project policy as grants.
    No input stream/file handles, filesystem writes, parser or network calls occur.
    """
    if not isinstance(source, bytes):
        raise ImportRejected("invalid_source")
    if not isinstance(policy, ArchivePolicy):
        raise ImportRejected("missing_policy")
    start = monotonic()

    def check():
        if cancelled():
            raise ImportRejected("cancelled")
        if monotonic() - start >= policy.max_seconds:
            raise ImportRejected("deadline_exceeded")

    check()
    if len(source) > policy.max_archive_bytes:
        raise ImportRejected("resource_exhausted")
    if not source.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        raise ImportRejected("unsupported_archive" if zipfile.is_zipfile(io.BytesIO(source)) else "invalid_archive")
    try:
        central_start, entry_count = _zip_envelope(source, policy)
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            check()
            infos = archive.infolist()
            if len(infos) != entry_count:
                raise ImportRejected("invalid_archive")
            if len(infos) > policy.max_entries:
                raise ImportRejected("resource_exhausted")
            _member_coverage(source, infos, central_start, check)
            seen: dict[str, bool] = {}
            explicit: set[str] = set()
            prepared = []
            for info in infos:
                check()
                path, directory = _name(info.orig_filename, policy.max_path_depth)
                key = path.casefold()
                parts = key.split("/")
                for depth in range(1, len(parts)):
                    parent = "/".join(parts[:depth])
                    if seen.get(parent) is False:
                        raise ImportRejected("path_conflict")
                    seen[parent] = True
                if key in explicit or (key in seen and (not directory or not seen[key])):
                    raise ImportRejected("path_conflict")
                seen[key] = directory
                explicit.add(key)
                _metadata(info, directory)
                extension = "." + path.rsplit("/", 1)[-1].rsplit(".", 1)[-1].casefold()
                if not directory and (extension not in policy.allowed_extensions or extension in _FORBIDDEN_EXTENSIONS):
                    raise ImportRejected("unsupported_content")
                prepared.append((info, path, directory))
            total = 0
            entries = []
            for info, path, directory in prepared:
                check()
                # stdlib checks local name, flags and overlapping member extents.
                with archive.open(info):
                    pass
                header = struct.unpack_from("<4s5H3I2H", source, info.header_offset)
                if header[0] != b"PK\x03\x04" or header[2] != info.flag_bits or header[3] != info.compress_type:
                    raise ImportRejected("invalid_archive")
                name_length, extra_length = header[-2:]
                extra_start = info.header_offset + 30 + name_length
                _extra_fields(source[extra_start:extra_start + extra_length])
                if not info.flag_bits & 8 and header[6:9] != (info.CRC, info.compress_size, info.file_size):
                    raise ImportRejected("invalid_archive")
                size = crc = 0
                digest = hashlib.sha256()
                prefix = bytearray()
                for block in _chunks(source, extra_start + extra_length, info.compress_size,
                                     info.compress_type, policy.chunk_bytes, check):
                    size += len(block)
                    total += len(block)
                    if (size > policy.max_entry_bytes or total > policy.max_total_bytes
                            or size > policy.max_compression_ratio * max(1, info.compress_size)):
                        raise ImportRejected("resource_exhausted")
                    digest.update(block)
                    crc = zlib.crc32(block, crc)
                    if len(prefix) < 512:
                        prefix.extend(block[:512 - len(prefix)])
                if size != info.file_size or crc != info.CRC or (directory and size):
                    raise ImportRejected("invalid_archive")
                _content_exclusions(bytes(prefix))
                entries.append(ArchiveEntry(relative_path=path, kind="directory" if directory else "file",
                                            size_bytes=size, compressed_bytes=info.compress_size, sha256=digest.hexdigest()))
            digest = hashlib.sha256()
            for position in range(0, len(source), policy.chunk_bytes):
                check()
                digest.update(source[position:position + policy.chunk_bytes])
            result = ArchiveInventory(inventory_id=inventory_id, created_at=created_at, policy_id=policy.policy_id,
                                      policy_sha256=hashlib.sha256(policy.model_dump_json().encode()).hexdigest(),
                                      archive_sha256=digest.hexdigest(), archive_bytes=len(source),
                                      entries=tuple(entries), total_bytes=total)
            check()
            return result
    except ImportRejected:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError, NotImplementedError,
            RuntimeError, UnicodeError, struct.error, ValueError):
        raise ImportRejected("invalid_archive") from None
