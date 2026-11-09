"""Pure supplied endpoint/DNS and byte-stream policy, never a generic fetcher.

Trusted adapters bind asset/version and supply actual connection addresses for
each hop. These checks alone cannot pin sockets or prevent DNS rebinding. A live
transport must pin checked IPs and bound DNS/connect/read time, including blocking
iterator calls: cooperative checks here cannot interrupt caller-owned blocking I/O.
"""
from collections.abc import Callable, Iterable, Mapping
import hashlib
import ipaddress
import re
import time
from urllib.parse import urlsplit

from geoai.contracts.imports import (
    ProviderAssetBinding, ProviderPolicy, ProviderRequestPlan, ProviderStreamReceipt,
)


class NetworkRejected(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class ProviderTransfer:
    """One adapter-owned transfer/retry chain with a monotonic total budget.

    Policy/binding are trusted admin/adapter values, never project permissions.
    Call check_request for every request including retry/redirect. Its returned
    header list replaces the caller headers; cross-origin requests receive none.
    inspect_stream hashes only and never publishes or retains partial content.
    """
    def __init__(self, policy: ProviderPolicy, binding: ProviderAssetBinding, *,
                 cancelled: Callable[[], bool] = lambda: False,
                 monotonic: Callable[[], float] = time.monotonic):
        if not isinstance(policy, ProviderPolicy):
            raise NetworkRejected("missing_policy")
        if not isinstance(binding, ProviderAssetBinding) or policy.provider_id != binding.provider_id:
            raise NetworkRejected("asset_mismatch")
        self._policy, self._binding = policy, binding
        self._cancelled, self._clock = cancelled, monotonic
        self._start = monotonic()
        self._requests = self._redirects = self._bytes = 0
        self._origin = None
        self._visited: set[bytes] = set()

    def _check(self, binding: ProviderAssetBinding):
        if binding != self._binding:
            raise NetworkRejected("asset_mismatch")
        if self._cancelled():
            raise NetworkRejected("cancelled")
        if self._clock() - self._start >= self._policy.max_seconds:
            raise NetworkRejected("deadline_exceeded")

    def check_request(self, binding: ProviderAssetBinding, url: str, addresses: tuple[str, ...], *,
                      headers: Mapping[str, str] | None = None, redirect: bool = False) -> ProviderRequestPlan:
        self._check(binding)
        if (not isinstance(url, str) or len(url) > self._policy.max_url_length or not url.isascii()
                or any(ord(char) <= 32 or ord(char) == 127 for char in url) or "\\" in url):
            raise NetworkRejected("endpoint_denied")
        try:
            endpoint = urlsplit(url)
            port = endpoint.port if endpoint.port is not None else (443 if endpoint.scheme == "https" else 80)
            origin = (endpoint.scheme, endpoint.hostname, port)
            if (not endpoint.hostname or endpoint.username is not None or endpoint.password is not None
                    or endpoint.fragment or "%" in endpoint.netloc or endpoint.netloc.endswith(":")
                    or origin not in {(item.scheme, item.host, item.port) for item in self._policy.endpoints}):
                raise NetworkRejected("endpoint_denied")
        except ValueError:
            raise NetworkRejected("endpoint_denied") from None
        if not isinstance(addresses, tuple) or not addresses:
            raise NetworkRejected("address_denied")
        if len(addresses) > self._policy.max_address_records:
            raise NetworkRejected("resource_exhausted")
        for value in addresses:
            if not isinstance(value, str):
                raise NetworkRejected("address_denied")
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                raise NetworkRejected("address_denied") from None
            private_allowed = (address.version == 4 and any(address in ipaddress.ip_network(cidr)
                                for cidr in self._policy.allowed_private_networks))
            if (address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified
                    or address.is_reserved or getattr(address, "ipv4_mapped", None) is not None
                    or (address.version == 6 and any(address in ipaddress.ip_network(cidr) for cidr in
                        ("64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32")))
                    or (not address.is_global and not private_allowed)):
                raise NetworkRejected("address_denied")
            # IP literals must bind to that exact address, not caller-supplied DNS.
            try:
                literal = ipaddress.ip_address(endpoint.hostname)
            except ValueError:
                literal = None
            if literal is not None and literal != address:
                raise NetworkRejected("address_denied")
        if self._requests >= self._policy.max_requests or (redirect and self._redirects >= self._policy.max_redirects):
            raise NetworkRejected("resource_exhausted")
        if redirect and not self._requests:
            raise NetworkRejected("invalid_redirect")
        identity = hashlib.sha256(url.encode("ascii")).digest()
        if redirect and identity in self._visited:
            raise NetworkRejected("redirect_loop")
        if headers is not None and not isinstance(headers, Mapping):
            raise NetworkRejected("invalid_headers")
        for key, value in (headers or {}).items():
            if (not isinstance(key, str) or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", key)
                    or not isinstance(value, str) or any(ord(char) < 32 or ord(char) == 127 for char in value)):
                raise NetworkRejected("invalid_headers")
        forwarded = tuple((headers or {}).items()) if self._origin in (None, origin) else ()
        plan = ProviderRequestPlan(binding=binding, origin=origin, headers=forwarded)
        self._requests += 1
        self._redirects += int(redirect)
        self._origin = origin
        self._visited.add(identity)
        return plan

    def inspect_stream(self, binding: ProviderAssetBinding, chunks: Iterable[bytes], *,
                       declared_length: int | None = None) -> ProviderStreamReceipt:
        self._check(binding)
        if not self._requests:
            raise NetworkRejected("invalid_stream")
        if declared_length is not None:
            if type(declared_length) is not int or declared_length < 0:
                raise NetworkRejected("invalid_stream")
            if declared_length > self._policy.max_bytes - self._bytes:
                raise NetworkRejected("resource_exhausted")
        digest = hashlib.sha256()
        size = 0
        try:
            for block in chunks:
                self._check(binding)
                if not isinstance(block, bytes):
                    raise NetworkRejected("invalid_stream")
                self._bytes += len(block)
                size += len(block)
                if len(block) > self._policy.max_chunk_bytes or self._bytes > self._policy.max_bytes:
                    raise NetworkRejected("resource_exhausted")
                if declared_length is not None and size > declared_length:
                    raise NetworkRejected("invalid_stream")
                digest.update(block)
        except NetworkRejected:
            raise
        except Exception:
            # Transport/iterator messages and response bodies may contain secrets.
            raise NetworkRejected("stream_failed") from None
        self._check(binding)
        if declared_length is not None and declared_length != size:
            raise NetworkRejected("invalid_stream")
        return ProviderStreamReceipt(binding=binding, size_bytes=size, sha256=digest.hexdigest())

    def classify_failure(self, binding: ProviderAssetBinding, status: int) -> str:
        """Classify only; adapters still enforce request/deadline budget on retries."""
        self._check(binding)
        if status in (401, 403):
            return "refresh_credentials"
        if status == 429:
            return "retry_quota"
        if status in (500, 502, 503, 504):
            return "retry_provider"
        return "no_retry"
