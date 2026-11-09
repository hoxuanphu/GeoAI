"""Local API authorization boundaries; no native lifecycle or inference claims."""
import importlib
import unittest
import io
import logging

import asyncio
import httpx


class Client:
    """Sync facade over the supported async ASGI transport; no server double."""
    def __init__(self, app, base_url):
        self.app, self.base_url = app, base_url
    def request(self, method, path, **kwargs):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url=self.base_url) as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(run())
    def get(self, path, **kwargs): return self.request("GET", path, **kwargs)
    def options(self, path, **kwargs): return self.request("OPTIONS", path, **kwargs)
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

try:
    session_module = importlib.import_module("geoai.api.session")
    app_module = importlib.import_module("geoai.api.app")
except ModuleNotFoundError as exc:
    if exc.name not in {"geoai.api", "geoai.api.session", "geoai.api.app"}:
        raise
    session_module = app_module = None


class LocalSessionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(session_module, "Local session boundary is not implemented")
        self.assertIsNotNone(app_module, "Local API routes are not implemented")
        self.token = "synthetic-session-current-0123456789abcdef"
        self.policy = session_module.SessionPolicy(
            token=self.token,
            port=49231,
            allowed_origins=("tauri://localhost", "http://tauri.localhost"),
            allow_missing_origin=True,
        )
        self.client = Client(app_module.create_app(self.policy), base_url="http://127.0.0.1:49231")
        self.addCleanup(self.client.close)

    def headers(self, **extra):
        return {"Authorization": "Bearer " + self.token, "Origin": "tauri://localhost", **extra}

    def test_authorized_health_and_capabilities_describe_implemented_foundation(self):
        response = self.client.get("/v1/health", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["schema_version"], "0.1.0")
        self.assertTrue(response.json()["app_version"])
        capabilities = self.client.get("/v1/capabilities", headers=self.headers())
        self.assertEqual(capabilities.status_code, 200)
        self.assertNotIn(self.token, capabilities.text)
        self.assertNotIn(self.token, response.text)

    def test_missing_wrong_and_previous_session_tokens_are_rejected(self):
        for authorization in (None, "Bearer wrong", "Bearer synthetic-previous-session", "Basic " + self.token):
            headers = {"Origin": "tauri://localhost"}
            if authorization is not None:
                headers["Authorization"] = authorization
            with self.subTest(authorization=authorization):
                response = self.client.get("/v1/health", headers=headers)
                self.assertEqual(response.status_code, 401)
                self.assertNotIn(self.token, response.text)

    def test_wrong_host_and_wrong_port_are_rejected_even_with_token(self):
        for host in ("attacker.example", "127.0.0.1:49232", "127.0.0.1.attacker.example:49231", "localhost:49231"):
            with self.subTest(host=host):
                response = self.client.get("/v1/health", headers=self.headers(Host=host))
                self.assertEqual(response.status_code, 403)

    def test_wrong_or_null_origin_is_rejected_even_with_token(self):
        for origin in ("https://attacker.example", "null", "tauri://localhost.attacker.example", "http://127.0.0.1:1420"):
            with self.subTest(origin=origin):
                response = self.client.get("/v1/health", headers=self.headers(Origin=origin))
                self.assertEqual(response.status_code, 403)

    def test_missing_origin_requires_explicit_policy_and_valid_token(self):
        headers = {"Authorization": "Bearer " + self.token}
        self.assertEqual(self.client.get("/v1/health", headers=headers).status_code, 200)
        strict = session_module.SessionPolicy(
            token=self.token, port=49231,
            allowed_origins=("tauri://localhost",), allow_missing_origin=False,
        )
        with Client(app_module.create_app(strict), base_url="http://127.0.0.1:49231") as client:
            self.assertEqual(client.get("/v1/health", headers=headers).status_code, 403)
        self.assertEqual(self.client.get("/v1/health").status_code, 401)

    def test_query_parameter_does_not_grant_access(self):
        response = self.client.get("/v1/health", params={"token": self.token}, headers={"Origin": "tauri://localhost"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(self.token, response.text)

    def test_invalid_origin_preflight_is_rejected(self):
        response = self.client.options("/v1/health", headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        })
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_authorization_header_name_is_case_insensitive(self):
        response = self.client.get("/v1/health", headers={
            "authorization": "Bearer " + self.token, "origin": "tauri://localhost",
        })
        self.assertEqual(response.status_code, 200)

    def test_duplicate_sensitive_headers_cannot_bypass_policy(self):
        for name, first, second in (("Authorization", "Bearer wrong", "Bearer " + self.token), ("Host", "attacker.example", "127.0.0.1:49231"), ("Origin", "https://attacker.example", "tauri://localhost")):
            headers = list(self.headers().items()) + [(name, first), (name.lower(), second)]
            self.assertEqual(self.client.get("/v1/health", headers=headers).status_code, 403)

    def test_valid_preflight_grants_cors_only_and_actual_get_still_needs_token(self):
        response = self.client.options("/v1/health", headers={"Origin": "tauri://localhost", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["access-control-allow-origin"], "tauri://localhost")
        self.assertEqual(self.client.get("/v1/health", headers={"Origin": "tauri://localhost"}).status_code, 401)
        for extra in ({"Access-Control-Request-Headers": "authorization,x-other"}, {"Access-Control-Request-Method": "POST"}, {"Host": "attacker.example"}):
            headers = {"Origin": "tauri://localhost", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization", **extra}
            self.assertEqual(self.client.options("/v1/health", headers=headers).status_code, 403)

    def test_logs_redact_request_targets_headers_and_exception_text(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.addFilter(session_module.SanitizedLogFilter())
        logger = logging.Logger("synthetic")
        logger.addHandler(handler)
        try:
            raise ValueError(self.token)
        except ValueError:
            logger.exception("GET https://example.invalid/?token=%s Authorization: Bearer %s", self.token, self.token)
        self.assertNotIn(self.token, output.getvalue())
        self.assertNotIn("https://", output.getvalue())
        self.assertNotIn("Authorization", output.getvalue())
        self.assertTrue(output.getvalue())


if __name__ == "__main__":
    unittest.main()
