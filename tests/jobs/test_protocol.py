import unittest

from geoai.jobs.protocol import MAX_FRAME_BYTES, JsonLines, ProtocolError, classify, correlate_response, encode
from geoai.contracts.rpc import RpcFailure, RpcNotification, RpcRequest, RpcSuccess


class ProtocolTests(unittest.TestCase):
    def test_split_utf8_and_multiple_frames(self):
        reader = JsonLines()
        first = b'{"jsonrpc":"2.0","id":1,"method":"shutdown","params":{"graceful":true}}\n'
        second = '{"jsonrpc":"2.0","id":"é","result":{"accepted":true}}\n'.encode()
        self.assertEqual(reader.feed(first + second[:-3]), [__import__('json').loads(first)])
        self.assertEqual(reader.feed(second[-3:]), [__import__('json').loads(second)])
        reader.finish()

    def test_exact_limit_and_poison(self):
        line = b'{"x":"' + b'a' * 7 + b'"}\n'
        self.assertEqual(len(line), 16)
        self.assertEqual(JsonLines(16).feed(line), [{"x": "a" * 7}])
        reader = JsonLines(15)
        with self.assertRaises(ProtocolError): reader.feed(line)
        with self.assertRaises(ProtocolError): reader.feed(b'{}\n')
        with self.assertRaises(ProtocolError): JsonLines(16).feed(b'x' * 100000)

    def test_invalid_json_forms_and_eof(self):
        for raw in (b'\n', b'[]\n', b'\xff\n', b'{"x":1,"x":2}\n',
                    b'{"x":NaN}\n', b'{"x":1e999}\n', b'{"x":"\\ud800"}\n'):
            with self.subTest(raw=raw), self.assertRaises(ProtocolError): JsonLines().feed(raw)
        reader = JsonLines()
        reader.feed(b'{')
        with self.assertRaises(ProtocolError): reader.finish()
        with self.assertRaises(ProtocolError): JsonLines().feed(b'{"x":' + b'[' * 1200 + b'0' + b']' * 1200 + b'}\n')

    def test_encode_rejects_nonfinite_surrogate_and_size(self):
        for value in ({"x": float('inf')}, {"x": '\ud800'}):
            with self.assertRaises(ValueError): encode(value)
        self.assertEqual(encode({"x": 1}), b'{"x":1}\n')
        with self.assertRaises(ValueError): encode({"x": 1}, max_bytes=7)
        with self.assertRaises(ValueError): encode({"x": "a" * MAX_FRAME_BYTES}, max_bytes=2_000_000)
        deep = 0
        for _ in range(260): deep = [deep]
        with self.assertRaises(ValueError): encode({"x": deep})

    def test_envelope_precedes_method_and_params(self):
        bad = {"jsonrpc": "1.0", "id": 3, "method": "unknown", "params": []}
        self.assertEqual(classify(bad).error.code, -32600)
        self.assertEqual(classify({"jsonrpc":"2.0","id":3,"method":"unknown","params":{}}).error.code, -32601)
        self.assertEqual(classify({"jsonrpc":"2.0","id":3,"method":"shutdown","params":{}}).error.code, -32602)
        self.assertEqual(classify({"jsonrpc":"2.0","id":3,"method":"shutdown"}).error.code, -32602)
        self.assertEqual(classify({"jsonrpc":"2.0","id":3,"method":"shutdown","params":[]}).error.code, -32602)
        self.assertEqual(classify({"jsonrpc":"2.0","id":True,"method":"shutdown","params":{"graceful":True}}).error.code, -32600)

    def test_versions_response_and_notifications(self):
        req = {"jsonrpc":"2.0","id":"a","method":"capabilities","params":{"protocol_version":"2","schema_version":"0.1.0"}}
        self.assertEqual(classify(req).error.data.code, 'unsupported_schema')
        self.assertIsInstance(classify({"jsonrpc":"2.0","id":1,"method":"shutdown","params":{"graceful":True}}), RpcRequest)
        self.assertIsInstance(classify({"jsonrpc":"2.0","id":1,"result":{"accepted":True}}), RpcSuccess)
        self.assertEqual(classify({"jsonrpc":"2.0","id":1,"result":{},"error":{"code":-32603,"message":"x"}}).error.code, -32600)
        event = {"jsonrpc":"2.0","method":"heartbeat","params":{"attempt":{"job_id":"job:1","attempt_id":"attempt:1","generation_token":"generation:1"}}}
        self.assertIsInstance(classify(event), RpcNotification)
        with self.assertRaises(ProtocolError): classify({**event, "id": 1})
        with self.assertRaises(ProtocolError): classify({**event, "method": "unknown"})

    def test_response_correlation_and_failure_envelopes(self):
        success = classify({"jsonrpc":"2.0","id":"start:1","result":{"accepted":True}})
        self.assertIs(correlate_response(success, "start:1"), success)
        with self.assertRaises(ProtocolError): correlate_response(success, "start:2")
        with self.assertRaises(ProtocolError): correlate_response(success, True)
        failure = classify({"jsonrpc":"2.0","id":7,"error":{"code":-32001,"message":"Unsupported","data":{"code":"unsupported_schema","message":"Unsupported","retryable":False}}})
        self.assertIsInstance(failure, RpcFailure)
        self.assertIs(correlate_response(failure, 7), failure)
        self.assertEqual(classify({"jsonrpc":"2.0","id":7,"error":{"code":-32001,"message":"x"}}).error.code, -32600)

    def test_null_error_id_and_malformed_notification(self):
        from geoai.jobs.protocol import failure
        self.assertEqual(encode(failure(-32700, None)), b'{"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error","data":null}}\n')
        for value in ({"jsonrpc":"1.0","method":"heartbeat","params":{}},
                      {"jsonrpc":"2.0","method":"heartbeat","params":[],"extra":1}):
            with self.subTest(value=value), self.assertRaises(ProtocolError): classify(value)


if __name__ == '__main__': unittest.main()
