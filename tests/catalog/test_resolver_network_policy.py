"""Pure supplied endpoint/DNS/stream subsets of NET-01..06; no connections."""
from datetime import datetime, timezone
import importlib
import unittest

from pydantic import ValidationError

try:
    network = importlib.import_module("geoai.catalog.policy")
except ModuleNotFoundError:
    network = None

PROFILE = dict(created_at=datetime(2026, 11, 8, tzinfo=timezone.utc), policy_id="network:fixture-v1",
               provider_id="fixture", endpoints=(dict(scheme="https", host="data.example", port=443),
                                                dict(scheme="https", host="cdn.example", port=443)),
               allowed_private_networks=(), max_requests=3, max_redirects=1, max_bytes=8,
               max_seconds=1.0, max_chunk_bytes=4, max_address_records=4, max_url_length=1024)
BINDING = dict(provider_id="fixture", asset_id="fixture:asset-1", version_id="version:1")


class ProviderPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(network, "pure provider policy missing")
        from geoai.contracts.imports import ProviderPolicy, ProviderAssetBinding
        self.Policy, self.Binding = ProviderPolicy, ProviderAssetBinding
        self.binding = self.Binding(**BINDING)

    def transfer(self, profile=None, **kwargs):
        return network.ProviderTransfer(self.Policy(**{**PROFILE, **(profile or {})}), self.binding, **kwargs)

    def request(self, transfer, url="https://data.example/a?signature=secret", addresses=("8.8.8.8",), **kwargs):
        return transfer.check_request(self.binding, url, addresses, **kwargs)

    def rejected(self, code, action):
        with self.assertRaises(network.NetworkRejected) as caught:
            action()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)
        self.assertIsNone(caught.exception.__cause__)

    def test_allowlisted_asset_and_endpoint_pass_without_exposing_url(self):
        transfer = self.transfer()
        plan = self.request(transfer, headers={"Authorization": "secret", "Range": "bytes=0-3"})
        self.assertEqual(plan.origin, ("https", "data.example", 443))
        self.assertEqual(plan.binding, self.binding)
        self.assertIn(("Authorization", "secret"), plan.headers)
        self.assertNotIn("signature", repr(plan))
        self.assertNotIn("secret", plan.model_dump_json())
        receipt = transfer.inspect_stream(self.binding, (b"ab", b"c"), declared_length=3)
        self.assertEqual(receipt.size_bytes, 3)
        self.assertEqual(receipt.sha256, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_missing_profile_identity_mismatch_arbitrary_url_and_malformed_origins_fail_closed(self):
        self.rejected("missing_policy", lambda: network.ProviderTransfer(None, self.binding))
        for url in ("http://data.example/a", "https://evil.example/a", "https://data.example:444/a",
                    "https://user:secret@data.example/a", "file:///a", "https://data.example./a",
                    "https://data.example\\@evil.example/a", "https://data.example/a\n",
                    "https://data.example:bad/a", "https://data.example:0/a", "https://data.example:/a",
                    "https://data.example/a#secret"):
            with self.subTest(url=url):
                self.rejected("endpoint_denied", lambda: self.request(self.transfer(), url))
        transfer = self.transfer()
        wrong = self.Binding(**{**BINDING, "version_id": "version:2"})
        self.rejected("asset_mismatch", lambda: transfer.check_request(wrong, "https://data.example/a", ("8.8.8.8",)))
        with self.assertRaises(ValidationError):
            self.Binding(**{**BINDING, "asset_id": "other:asset-1"})

    def test_all_supplied_dns_addresses_must_be_public_and_record_count_is_bounded(self):
        for addresses in ((), ("127.0.0.1",), ("10.0.0.1",), ("169.254.169.254",),
                          ("::1",), ("::ffff:127.0.0.1",), ("fe80::1",), ("100.64.0.1",),
                          ("64:ff9b::7f00:1",), ("2002:7f00:1::",),
                          ("8.8.8.8", "192.168.1.1"), ("not-an-address",)):
            with self.subTest(addresses=addresses):
                self.rejected("address_denied", lambda: self.request(self.transfer(), addresses=addresses))
        self.rejected("resource_exhausted", lambda: self.request(self.transfer(profile={"max_address_records": 1}), addresses=("8.8.8.8", "1.1.1.1")))
        self.request(self.transfer(), addresses=("2606:4700:4700::1111",))

    def test_trusted_rfc1918_profile_allows_only_its_private_subnet_never_control_loopback(self):
        transfer = self.transfer(profile={"allowed_private_networks": ("10.20.0.0/16",)})
        self.request(transfer, addresses=("10.20.3.4",))
        self.rejected("address_denied", lambda: self.request(transfer, addresses=("10.21.0.1",)))
        self.rejected("address_denied", lambda: self.request(transfer, addresses=("127.0.0.1",)))
        for cidr in ("0.0.0.0/0", "127.0.0.0/8", "169.254.0.0/16", "fc00::/7"):
            with self.subTest(cidr=cidr), self.assertRaises(ValidationError):
                self.Policy(**{**PROFILE, "allowed_private_networks": (cidr,)})

    def test_every_redirect_is_checked_and_cross_origin_drops_all_forwarded_headers(self):
        transfer = self.transfer()
        self.request(transfer)
        plan = self.request(transfer, "https://cdn.example/file", headers={"Authorization": "secret", "Cookie": "secret", "X-Vendor-Token": "secret"}, redirect=True)
        self.assertEqual(plan.headers, ())
        self.rejected("resource_exhausted", lambda: self.request(transfer, "https://data.example/next", redirect=True))
        transfer = self.transfer()
        self.request(transfer)
        self.rejected("endpoint_denied", lambda: self.request(transfer, "https://evil.example/secret", redirect=True))
        transfer = self.transfer()
        self.request(transfer)
        self.rejected("redirect_loop", lambda: self.request(transfer, redirect=True))

    def test_actual_stream_budget_length_request_budget_deadline_and_cancel(self):
        transfer = self.transfer()
        self.request(transfer)
        self.rejected("resource_exhausted", lambda: transfer.inspect_stream(self.binding, (b"abcd", b"efgh", b"i")))
        transfer = self.transfer()
        self.request(transfer)
        self.rejected("invalid_stream", lambda: transfer.inspect_stream(self.binding, (b"abc",), declared_length=2))
        transfer = self.transfer()
        self.request(transfer)
        self.rejected("resource_exhausted", lambda: transfer.inspect_stream(self.binding, (b"abcde",)))
        transfer = self.transfer(profile={"max_requests": 1})
        self.request(transfer)
        self.rejected("resource_exhausted", lambda: self.request(transfer))
        self.rejected("cancelled", lambda: self.request(self.transfer(cancelled=lambda: True)))
        ticks = iter((0.0, 0.1, 0.2, 1.2))
        transfer = self.transfer(monotonic=lambda: next(ticks))
        self.request(transfer)
        self.rejected("deadline_exceeded", lambda: transfer.inspect_stream(self.binding, (b"a", b"b")))

    def test_retry_classification_keeps_same_asset_version_and_never_consumes_unlimited_requests(self):
        transfer = self.transfer()
        for status, decision in ((401, "refresh_credentials"), (403, "refresh_credentials"),
                                 (429, "retry_quota"), (503, "retry_provider"), (404, "no_retry")):
            self.assertEqual(transfer.classify_failure(self.binding, status), decision)
        wrong = self.Binding(**{**BINDING, "asset_id": "fixture:another-scene"})
        self.rejected("asset_mismatch", lambda: transfer.classify_failure(wrong, 401))

    def test_headers_cannot_inject_fields_or_leak_in_validation_errors(self):
        for headers in ({"Authorization": "secret\r\nInjected: yes"}, {"Bad\nName": "secret"}, {"Authorization": object()}):
            self.rejected("invalid_headers", lambda: self.request(self.transfer(), headers=headers))

    def test_iterator_failure_is_sanitized_and_partial_bytes_remain_in_total_budget(self):
        def broken():
            yield b"abcd"
            raise OSError("https://signed.example/?credential=secret")
        transfer = self.transfer(profile={"max_bytes": 6})
        self.request(transfer)
        self.rejected("stream_failed", lambda: transfer.inspect_stream(self.binding, broken()))
        self.request(transfer)
        self.rejected("resource_exhausted", lambda: transfer.inspect_stream(self.binding, (b"abc",)))


if __name__ == "__main__":
    unittest.main()
