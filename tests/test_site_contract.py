"""Independent site contract regressions; no OS checkout, network or secrets."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
from public_release_catalog import render_catalog, PublicReleaseCatalogError
from site_routes import load_routes
from site_seo import validate_origin, render_html

class SiteContractTests(unittest.TestCase):
    def test_owner_and_routes(self):
        report = build.check_source(strict_assets=False)
        self.assertGreater(report["source_files"], 25)
        self.assertEqual(len(build.ROUTES), 11)
        self.assertEqual(len(set(build.ROUTES)), len(build.ROUTES))

    def test_live_auth_is_not_activated_by_static_source(self):
        data = json.loads((ROOT / "site/config/public-site.json").read_text(encoding="utf-8"))
        self.assertFalse(data["legal"]["account_activation_ready"])
        self.assertFalse(data["product"]["web"]["enabled"])
        self.assertIsNone(data["identity"]["recovery_url"])
        self.assertIsNone(data["identity"]["recovery_complete_url"])
        self.assertEqual(data["downloads"]["catalog_url"], "/releases/catalog.json")

    def test_brand_not_implicitly_read_from_os(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                build.stage_brand(Path(tmp), Path(tmp) / "nonexistent")
        self.assertNotIn("system/surface/", (ROOT / "scripts/build.py").read_text().split("def stage_brand(")[1].split("def build(")[0])

    def test_unauthorized_catalog_fails_closed(self):
        result = render_catalog({"releases": []})
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["releases"], [])
        with self.assertRaises(PublicReleaseCatalogError):
            render_catalog({"releases": [{"release_id": "0" * 40, "public_authorized": False}]})

    def test_path_boundaries(self):
        for value in ("/auth/login", "/download/release.bin", "/terms/"):
            self.assertTrue(build.safe_relative(value))
        for value in ("https://example.com", "//host/auth", "/../auth", "/foo?bar", "/foo#bar", r"/foo\bar"):
            self.assertFalse(build.safe_relative(value))

    def test_original_asset_provenance_is_locked(self):
        # Missing images block the distributable build; do not replace them with
        # placeholders or fake marketing graphics just to make CI green.
        result = build.check_source(strict_assets=False)
        missing = set(result["missing_source_assets"])
        self.assertTrue(missing.issubset(set(build.BINARY_PROVENANCE)))
        if missing:
            with self.assertRaises(build.SiteError):
                build.check_source(strict_assets=True)
        else:
            self.assertFalse(build.check_source(strict_assets=True)["missing_source_assets"])

    def test_route_ssot_and_sensitive_indexing(self):
        routes = load_routes()
        self.assertEqual(len(routes), 11)
        self.assertEqual(tuple(route["source"] for route in routes), build.ROUTES)
        self.assertEqual(sum(route["indexable"] for route in routes), 5)
        for route in routes:
            self.assertTrue((ROOT / "site" / route["source"]).is_file())
            if route["path"] in ("/conta/", "/login/", "/cadastro/", "/recuperar/",
                                 "/recuperar/nova-senha/", "/web/"):
                self.assertFalse(route["indexable"])

    def test_seo_origin_is_explicit_and_https_only(self):
        self.assertEqual(validate_origin("https://ordax.com.br"), "https://ordax.com.br")
        for invalid in ("http://ordax.com.br", "https://ordax.com.br/",
                        "https://ordax.com.br/path", "https://ordax.com.br?redirect=x",
                        "https://user:pass@ordax.com.br", "https://ordax..com",
                        "//ordax.com.br", "https://ordax.com.br:8443"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_origin(invalid)

    def test_seo_gated_route_cannot_become_indexable(self):
        routes = {record["path"]: record for record in load_routes()}
        html = '<html><head><title>Site</title><meta name="description" content="Portal"></head><body></body></html>'
        public = render_html(html, routes["/"], "https://ordax.com.br")
        self.assertIn('<link rel="canonical" href="https://ordax.com.br/">', public)
        self.assertIn('property="og:url"', public)
        gated = render_html(html, routes["/login/"], "https://ordax.com.br")
        self.assertIn('content="noindex, nofollow"', gated)
        self.assertNotIn('rel="canonical"', gated)

    def test_landing_uses_one_fixture_and_one_main_landmark(self):
        landing = (ROOT / "site/index.html").read_text("utf-8")
        controller = (ROOT / "site/assets/playground.js").read_text("utf-8")
        self.assertNotIn('id="playground-fixture"', landing)
        self.assertIn('fetch("/assets/playground-fixture.json"', controller)
        self.assertIn("for (const nestedMain of screen.querySelectorAll('main'))", controller)

    def test_site_is_not_native_web_surface(self):
        paths = (ROOT / "site").rglob("*")
        self.assertFalse(any("node_modules" in x.parts or ".env.production" in x.parts for x in paths))
        self.assertFalse((ROOT / "site/system").exists())
        self.assertFalse((ROOT / "site/tools/surface-web").exists())

if __name__ == "__main__":
    unittest.main()
