"""No-network negative tests for the opt-in staging gateway preflight."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from staging_preflight import (
    StagingPreflightError,
    evaluate_gateway_contracts,
    validate_staging_origin,
)

CONFIG = {
    "$schema": "prototype-ordax.public-site-runtime/1",
    "downloads": {"catalog_url": "/releases/catalog.json"},
    "product": {"web": {"enabled": False}},
    "legal": {"account_activation_ready": False, "auth_only_source_enabled": True},
}
SESSION = {
    "$schema": "prototype-ordax.public-identity-session/1",
    "provider": "supabase", "authenticated": False, "status": "anonymous",
}
CATALOG = {
    "$schema": "prototype-ordax.public-release-catalog/1",
    "status": "empty", "releases": [],
}


def make_fetch(overrides=None):
    responses = {
        "/config/public-site.json": (200, CONFIG),
        "/auth/session": (200, SESSION),
        "/releases/catalog.json": (200, CATALOG),
    }
    responses.update(overrides or {})
    observed = []

    def fetch(path, maximum):
        observed.append((path, maximum))
        status, payload = responses[path]
        return status, copy.deepcopy(payload)

    return fetch, observed


class StagingPreflightTests(unittest.TestCase):
    def test_only_explicit_staging_https_is_allowed(self):
        for candidate in (
            "http://staging.example.org", "https://ordax.com.br",
            "https://www.ordax.com.br", "https://localhost",
            "https://127.0.0.1", "https://[::1]",
            "https://example.org", "https://staging.example.org/other",
            "https://staging.example.org?token=abc",
            "https://user:password@staging.example.org",
            "https://staging.example.org:8080",
        ):
            with self.subTest(candidate=candidate), self.assertRaises(StagingPreflightError):
                validate_staging_origin(candidate)
        self.assertEqual(validate_staging_origin("https://staging.example.org/"),
                         "https://staging.example.org")
        self.assertEqual(validate_staging_origin("https://ordax-site-test.vercel.app"),
                         "https://ordax-site-test.vercel.app")

    def test_valid_anonymous_staging_is_only_a_partial_pass(self):
        fetch, calls = make_fetch()
        result = evaluate_gateway_contracts(fetch)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["identity_mode"], "auth-only")
        self.assertEqual(result["catalog_status"], "empty")
        self.assertEqual(result["authenticated_e2e"], "NOT_TESTED")
        self.assertEqual(result["publisher_attestation"], "NOT_TESTED")
        self.assertFalse(result["production_approval"])
        self.assertEqual([path for path, _ in calls], [
            "/config/public-site.json", "/auth/session", "/releases/catalog.json"])

    def test_unavailable_active_gateway_is_never_reported_ready(self):
        bad = {
            "$schema": "prototype-ordax.public-site-proxy-error/1",
            "error": "account-gateway-unconfigured",
        }
        fetch, _ = make_fetch({"/auth/session": (503, bad)})
        with self.assertRaisesRegex(StagingPreflightError, "active-account-session-unavailable"):
            evaluate_gateway_contracts(fetch)

    def test_wrong_session_provider_or_authenticated_session_fails(self):
        for session in (
            {**SESSION, "provider": "gated"},
            {**SESSION, "authenticated": True, "status": "authenticated", "subject": "fake"},
        ):
            with self.subTest(session=session):
                fetch, _ = make_fetch({"/auth/session": (200, session)})
                with self.assertRaisesRegex(StagingPreflightError, "identity-contract"):
                    evaluate_gateway_contracts(fetch)

    def test_static_client_cannot_force_web_or_catalog_authority(self):
        for config in (
            {**CONFIG, "product": {"web": {"enabled": True}}},
            {**CONFIG, "downloads": {"catalog_url": "//malicious.example/catalog"}},
        ):
            with self.subTest(config=config):
                fetch, _ = make_fetch({"/config/public-site.json": (200, config)})
                with self.assertRaises(StagingPreflightError):
                    evaluate_gateway_contracts(fetch)

    def test_ready_or_malformed_release_catalog_is_refused(self):
        for value in (
            {**CATALOG, "status": "ready", "releases": [{"release_id": "invented"}]},
            {**CATALOG, "status": "empty", "releases": [{"release_id": "invented"}]},
            {**CATALOG, "status": "ready", "releases": []},
            {**CATALOG, "unexpected": "field"},
        ):
            with self.subTest(catalog=value):
                fetch, _ = make_fetch({"/releases/catalog.json": (200, value)})
                with self.assertRaisesRegex(StagingPreflightError, "catalog"):
                    evaluate_gateway_contracts(fetch)

    def test_missing_catalog_or_invalid_config_fails(self):
        fetch, _ = make_fetch({"/releases/catalog.json": (503, CATALOG)})
        with self.assertRaisesRegex(StagingPreflightError, "catalog-http-status"):
            evaluate_gateway_contracts(fetch)
        fetch, _ = make_fetch({"/config/public-site.json": (200, {**CONFIG, "$schema": "other"})})
        with self.assertRaisesRegex(StagingPreflightError, "site-runtime-contract"):
            evaluate_gateway_contracts(fetch)


if __name__ == "__main__":
    unittest.main()
