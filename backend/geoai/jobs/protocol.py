"""Bounded JSON-RPC framing and envelope classification.

This module deliberately has no transport, dispatch, persistence, or business logic.
"""
from __future__ import annotations

import json
import math
from typing import Any

from geoai.contracts.rpc import (
    RpcRequest, RpcNotification, RpcSuccess, RpcFailure, RpcError,
)

MAX_FRAME_BYTES = 1_048_576
MAX_JSON_DEPTH = 256
_METHODS = {"capabilities", "start", "cancel", "shutdown"}
_EVENTS = {"heartbeat", "progress", "artifact_candidate", "completed", "error"}

class ProtocolError(ValueError):
    """Fatal framing corruption; callers must stop reading the stream."""

class TruncatedFrame(ProtocolError):
    pass

class JsonLines:
    """Incremental UTF-8/LF reader with a bounded partial-line buffer."""
    def __init__(self, max_bytes: int = MAX_FRAME_BYTES):
        if type(max_bytes) is not int or max_bytes < 2 or max_bytes > MAX_FRAME_BYTES:
            raise ValueError("invalid frame bound")
        self.max_bytes = max_bytes
        self._buffer = bytearray()
        self.fatal = False

    def feed(self, data: bytes) -> list[Any]:
        if self.fatal:
            raise ProtocolError("reader is terminated")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("feed expects bytes")
        raw = bytes(data)
        out = []
        start = 0
        try:
            while True:
                pos = raw.find(b"\n", start)
                if pos < 0:
                    if len(self._buffer) + len(raw) - start + 1 > self.max_bytes:
                        raise ProtocolError("frame exceeds maximum size")
                    self._buffer.extend(raw[start:])
                    break
                if len(self._buffer) + pos + 1 - start > self.max_bytes:
                    raise ProtocolError("frame exceeds maximum size")
                self._buffer.extend(raw[start:pos + 1])
                line = bytes(self._buffer[:-1]); self._buffer.clear()
                if not line:
                    raise ProtocolError("blank frame")
                out.append(_decode_json(line))
                start = pos + 1
        except Exception:
            self.fatal = True
            self._buffer.clear()
            raise
        return out

    def finish(self) -> None:
        if self.fatal:
            raise ProtocolError("reader is terminated")
        if self._buffer:
            self.fatal = True; self._buffer.clear()
            raise TruncatedFrame("stream ended before LF")

def _decode_json(line: bytes) -> Any:
    try:
        text = line.decode("utf-8", errors="strict")
        def reject(v: str): raise ValueError("non-finite number")
        def pairs(items):
            d = {}
            for k, v in items:
                if k in d: raise ValueError("duplicate key")
                d[k] = v
            return d
        value = json.loads(text, parse_constant=reject, object_pairs_hook=pairs)
    except Exception as exc:
        raise ProtocolError("invalid JSON frame") from exc
    if not isinstance(value, dict):
        raise ProtocolError("JSON-RPC frame must be an object")
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_JSON_DEPTH:
            raise ProtocolError("JSON nesting exceeds limit")
        if isinstance(item, float) and not math.isfinite(item):
            raise ProtocolError("non-finite JSON number")
        if isinstance(item, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in item):
            raise ProtocolError("escaped surrogate is not valid wire text")
        if isinstance(item, dict):
            pending.extend((part, depth + 1) for part in item.keys())
            pending.extend((part, depth + 1) for part in item.values())
        elif isinstance(item, list):
            pending.extend((part, depth + 1) for part in item)
    return value

def encode(value: Any, max_bytes: int = MAX_FRAME_BYTES) -> bytes:
    if type(max_bytes) is not int or max_bytes < 2:
        raise ValueError("invalid frame bound")
    max_bytes = min(max_bytes, MAX_FRAME_BYTES)
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if not isinstance(value, dict):
        raise ValueError("wire value must be an object")
    try:
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("value is not finite JSON") from exc
    if len(raw) > max_bytes:
        raise ValueError("frame exceeds maximum size")
    try:
        _decode_json(raw[:-1])
    except ProtocolError as exc:
        raise ValueError("value is not valid wire JSON") from exc
    return raw

def classify(value: dict[str, Any]) -> RpcRequest | RpcNotification | RpcSuccess | RpcFailure:
    """Validate one decoded object, returning a typed message or safe failure."""
    if not isinstance(value, dict):
        return failure(-32600, None)
    if "method" in value and "id" not in value and (value.get("jsonrpc") != "2.0" or "result" in value or "error" in value or any(k not in {"jsonrpc", "method", "params"} for k in value)):
        raise ProtocolError("malformed notification envelope")
    if "method" not in value:
        if value.get("jsonrpc") != "2.0" or "id" not in value or ("result" in value) == ("error" in value):
            return failure(-32600, None)
        try:
            return RpcSuccess.model_validate(value) if "result" in value else RpcFailure.model_validate(value)
        except Exception:
            return failure(-32600, None)
    if value.get("jsonrpc") != "2.0" or "result" in value or "error" in value or any(k not in {"jsonrpc", "id", "method", "params"} for k in value):
        return failure(-32600, _safe_id(value.get("id")))
    method = value.get("method")
    if not isinstance(method, str):
        return failure(-32600, _safe_id(value.get("id")))
    if "id" in value and not _valid_id(value["id"]):
        return failure(-32600, None)
    if method in _EVENTS:
        if "id" in value:
            raise ProtocolError("events cannot carry an id")
        if "params" not in value or not isinstance(value["params"], dict):
            raise ProtocolError("malformed notification")
        try: return RpcNotification.model_validate(value)
        except Exception as exc: raise ProtocolError("malformed event") from exc
    if "id" not in value:
        raise ProtocolError("unknown notification")
    if method not in _METHODS:
        return failure(-32601, value["id"])
    if "params" not in value or not isinstance(value["params"], dict):
        return failure(-32602, value["id"])
    if method == "capabilities":
        params = value.get("params")
        if set(params) == {"protocol_version", "schema_version"} and all(isinstance(params[k], str) for k in params) and (params["protocol_version"] != "0.1.0" or params["schema_version"] != "0.1.0"):
            return failure(-32001, value["id"])
    try: return RpcRequest.model_validate(value)
    except Exception: return failure(-32602, value["id"])

def _valid_id(v: Any) -> bool: return (isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool)))
def _safe_id(v: Any): return v if _valid_id(v) else None

def correlate_response(message: RpcSuccess | RpcFailure, expected_id: str | int) -> RpcSuccess | RpcFailure:
    """Match a validated response to one outstanding request ID; caller owns pending IDs."""
    if not isinstance(message, (RpcSuccess, RpcFailure)) or not _valid_id(expected_id) or message.id != expected_id or type(message.id) is not type(expected_id):
        raise ProtocolError("uncorrelated response")
    return message

def failure(code: int, ident: Any) -> RpcFailure:
    data = None
    if code == -32001:
        data = {"code": "unsupported_schema", "message": "Unsupported schema version", "retryable": False}
    return RpcFailure(jsonrpc="2.0", id=ident, error=RpcError(code=code, message={-32600:"Invalid Request",-32601:"Method not found",-32602:"Invalid params",-32603:"Internal error",-32700:"Parse error"}.get(code,"Protocol error"), data=data))

