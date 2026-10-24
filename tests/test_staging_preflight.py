"""Offline regression tests for Site-bundle-pinned anonymous staging preflight."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build import SCHEMA as SITE_BUNDLE_SCHEMA
from staging_preflight import (
    StagingPreflightError,
    evaluate_gateway_contracts,
    validate_staging_origin,
)

SITE_COMMIT = "1" * 40
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


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def make_fetch(overrides=None):
    """Build a pinned Site fixture from the chosen served config/catalog."""
    responses = {
        "/config/public-site.json": (200, CONFIG),
        "/auth/session": (200, SESSION),
        "/releases/catalog.json": (200, CATALOG),
    }
    responses.update(overrides or {})
    inventory = []
    for path in ("config/public-site.json", "releases/catalog.json"):
        item = responses["/" + path][1]
        inventory.append({"path": path, "sha256": digest(item), "size": len(encoded(item))})
    manifest = {
        "$schema": SITE_BUNDLE_SCHEMA,
        "source_commit": SITE_COMMIT,
        "artifact_class": "public-site",
        "catalog_status": "empty",
        "publications_sha256": None,
        "files": inventory,
    }
    responses["/public-site-manifest.json"] = (200, manifest)
    expected_manifest_sha256 = digest(manifest)
    observed = []

    def fetch(path, maximum):
        observed.append((path, maximum))
        status, payload = responses[path]
        return status, copy.deepcopy(payload), digest(payload), len(encoded(payload))

    return fetch, observed, expected_manifest_sha256


def prove(fetch, trusted_manifest_sha256):
    return evaluate_gateway_contracts(
        fetch,
        expected_site_commit=SITE_COMMIT,
        expected_manifest_sha256=trusted_manifest_sha256,
    )


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
            "https://staging.example.org:invalid",
        ):
            with self.subTest(candidate=candidate), self.assertRaises(StagingPreflightError):
                validate_staging_origin(candidate)
        self.assertEqual(validate_staging_origin("https://staging.example.org/"),
                         "https://staging.example.org")
        self.assertEqual(validate_staging_origin("https://ordax-site-test.vercel.app"),
                         "https://ordax-site-test.vercel.app")

    def test_valid_anonymous_staging_only_passes_pinned_bundle_and_contracts(self):
        fetch, calls, pin = make_fetch()
        result = prove(fetch, pin)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["candidate_source_commit"], SITE_COMMIT)
        self.assertEqual(result["identity_mode"], "auth-only")
        self.assertEqual(result["catalog_status"], "empty")
        self.assertEqual(result["authenticated_e2e"], "NOT_TESTED")
        self.assertEqual(result["publisher_attestation"], "NOT_TESTED")
        self.assertFalse(result["production_approval"])
        self.assertEqual([path for path, _ in calls], [
            "/public-site-manifest.json", "/config/public-site.json",
            "/auth/session", "/releases/catalog.json"
        ])

    def test_stale_os_bundle_or_mismatched_manifest_never_passes(self):
        fetch, calls, pin = make_fetch()
        with self.assertRaisesRegex(StagingPreflightError, "site-bundle-manifest-digest-mismatch"):
            prove(fetch, "0" * 64)
        self.assertEqual([path for path, _ in calls], ["/public-site-manifest.json"])
        fetch, _, pin = make_fetch({
            "/config/public-site.json": (200, CONFIG)
        })
        with self.assertRaisesRegex(StagingPreflightError, "expected-site-commit-invalid"):
            evaluate_gateway_contracts(fetch, expected_site_commit="old",
                                       expected_manifest_sha256=pin)
        with self.assertRaisesRegex(StagingPreflightError, "expected-site-manifest-sha256-invalid"):
            evaluate_gateway_contracts(fetch, expected_site_commit=SITE_COMMIT,
                                       expected_manifest_sha256="weak")

    def test_incorrect_site_source_commit_or_legacy_bundle_is_blocked(self):
        fetch, _, pin = make_fetch()
        with self.assertRaisesRegex(StagingPreflightError, "site-bundle-manifest-identity-invalid"):
            evaluate_gateway_contracts(fetch, expected_site_commit="2" * 40,
                                       expected_manifest_sha256=pin)

        def legacy(path, limit):
            if path == "/public-site-manifest.json":
                return 503, {"error": "missing"}, "0" * 64, 10
            raise AssertionError("must fail before reading legacy API")

        with self.assertRaisesRegex(StagingPreflightError, "site-bundle-manifest-digest-mismatch"):
            prove(legacy, pin)

    def test_published_config_and_catalog_must_match_bundle_inventory_bytes(self):
        fetch, _, pin = make_fetch()
        def tampered_config(path, maximum):
            status, payload, sha, size = fetch(path, maximum)
            if path == "/config/public-site.json":
                return status, payload, "f" * 64, size
            return status, payload, sha, size
        with self.assertRaisesRegex(StagingPreflightError, "site-bundle-file-mismatch:config"):
            prove(tampered_config, pin)

        def tampered_catalog(path, maximum):
            status, payload, sha, size = fetch(path, maximum)
            if path == "/releases/catalog.json":
                return status, payload, sha, size + 1
            return status, payload, sha, size
        with self.assertRaisesRegex(StagingPreflightError, "site-bundle-file-mismatch:releases"):
            prove(tampered_catalog, pin)

    def test_unavailable_active_gateway_is_never_reported_ready(self):
        bad = {"$schema": "prototype-ordax.public-site-proxy-error/1",
               "error": "account-gateway-unconfigured"}
        fetch, _, pin = make_fetch({"/auth/session": (503, bad)})
        with self.assertRaisesRegex(StagingPreflightError, "active-account-session-unavailable"):
            prove(fetch, pin)

    def test_unconfigured_gated_identity_cannot_claim_integration_ready(self):
        config = {**CONFIG, "legal": {
            "account_activation_ready": False, "auth_only_source_enabled": False
        }}
        gated = {**SESSION, "provider": "gated", "status": "unavailable"}
        fetch, _, pin = make_fetch({
            "/config/public-site.json": (200, config),
            "/auth/session": (200, gated),
        })
        with self.assertRaisesRegex(StagingPreflightError, "identity-gateway-still-gated"):
            prove(fetch, pin)

    def test_wrong_session_provider_or_authenticated_session_fails(self):
        for session in (
            {**SESSION, "provider": "gated"},
            {**SESSION, "authenticated": True, "status": "authenticated", "subject": "fake"},
        ):
            with self.subTest(session=session):
                fetch, _, pin = make_fetch({"/auth/session": (200, session)})
                with self.assertRaisesRegex(StagingPreflightError, "identity-contract"):
                    prove(fetch, pin)

    def test_static_client_cannot_force_web_or_catalog_authority(self):
        for config in (
            {**CONFIG, "product": {"web": {"enabled": True}}},
            {**CONFIG, "product": {"web": None}},
            {**CONFIG, "downloads": {"catalog_url": "//malicious.example/catalog"}},
            {**CONFIG, "downloads": None},
        ):
            with self.subTest(config=config):
                fetch, _, pin = make_fetch({"/config/public-site.json": (200, config)})
                with self.assertRaises(StagingPreflightError):
                    prove(fetch, pin)

    def test_ready_or_malformed_release_catalog_is_refused(self):
        for value in (
            {**CATALOG, "status": "ready", "releases": [{"release_id": "invented"}]},
            {**CATALOG, "status": "empty", "releases": [{"release_id": "invented"}]},
            {**CATALOG, "status": "ready", "releases": []},
            {**CATALOG, "unexpected": "field"},
        ):
            with self.subTest(catalog=value):
                fetch, _, pin = make_fetch({"/releases/catalog.json": (200, value)})
                with self.assertRaisesRegex(StagingPreflightError, "catalog"):
                    prove(fetch, pin)

    def test_missing_catalog_or_invalid_config_fails(self):
        fetch, _, pin = make_fetch({"/releases/catalog.json": (503, CATALOG)})
        with self.assertRaisesRegex(StagingPreflightError, "catalog-http-status"):
            prove(fetch, pin)
        fetch, _, pin = make_fetch({"/config/public-site.json": (200, {**CONFIG, "$schema": "other"})})
        with self.assertRaisesRegex(StagingPreflightError, "site-runtime-contract"):
            prove(fetch, pin)


if __name__ == "__main__":
    unittest.main()
