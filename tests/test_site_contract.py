"""Independent site contract regressions; no OS checkout, network or secrets."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build
from public_release_catalog import render_catalog, PublicReleaseCatalogError, _same_origin_path
from site_routes import load_routes
from site_seo import validate_origin, render_html
from smoke_static import check_css_dependencies

MIGRATION_LOCK = build.load_migration_lock(ROOT / "contracts/migration-artifact-lock.json")
BRAND_PIN = MIGRATION_LOCK["brand"]["manifest_sha256"]
OFFERS_PIN = MIGRATION_LOCK["offers"]["manifest_sha256"]
PREVIEW_PIN = MIGRATION_LOCK["surface_preview"]["manifest_sha256"]

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
            with self.assertRaises(build.SiteError):
                build.stage_brand(Path(tmp), Path(tmp) / "nonexistent", BRAND_PIN)
        self.assertNotIn("system/surface/", (ROOT / "scripts/build.py").read_text().split("def stage_brand(")[1].split("def build(")[0])

    def test_migration_lock_is_single_source_and_rejects_override(self):
        self.assertEqual(set(MIGRATION_LOCK), {"brand", "surface_preview", "offers"})
        self.assertEqual(MIGRATION_LOCK["brand"]["directory"],
                         ROOT / "artifacts/brand/os-migration-70b0f7eb")
        self.assertEqual(MIGRATION_LOCK["offers"]["directory"],
                         ROOT / "artifacts/offers/os-migration-70b0f7eb")
        with tempfile.TemporaryDirectory() as tmp:
            forged_path = Path(tmp) / "migration.json"
            original = json.loads((ROOT / "contracts/migration-artifact-lock.json").read_text("utf-8"))
            original["status"] = "official"
            forged_path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "lock"):
                build.load_migration_lock(forged_path)
            original["status"] = build.MIGRATION_STATUS
            original["artifacts"]["brand"]["directory"] = "../../secrets"
            forged_path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "lock"):
                build.load_migration_lock(forged_path)

    def test_all_migration_inputs_need_independent_hash_pins(self):
        brand = ROOT / "artifacts/brand/os-migration-70b0f7eb"
        offers = ROOT / "artifacts/offers/os-migration-70b0f7eb"
        self.assertEqual(build.digest((brand / "manifest.json").read_bytes()), BRAND_PIN)
        self.assertEqual(build.digest((offers / "manifest.json").read_bytes()), OFFERS_PIN)
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            stage.mkdir()
            receipt = build.stage_brand(stage, brand, BRAND_PIN)
            self.assertEqual(receipt["manifest_sha256"], BRAND_PIN)
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.stage_brand(stage, brand, None)
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.stage_brand(stage, brand, "0" * 64)

            html, offer_receipt = build.load_reference_offers(offers, OFFERS_PIN)
            self.assertIn("Planos em preparação", html)
            self.assertEqual(offer_receipt["manifest_sha256"], OFFERS_PIN)
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.load_reference_offers(offers, None)
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.load_reference_offers(offers, "0" * 64)
            with self.assertRaises(build.SiteError):
                build.load_reference_offers(None, OFFERS_PIN)

            # Tamper with payload and rewrite *self-declared* hash in manifest:
            # the independent pin still rejects the malicious new manifest.
            modified = Path(tmp) / "brand-forged"
            shutil.copytree(brand, modified)
            forged = json.loads((modified / "manifest.json").read_text("utf-8"))
            forged["status"] = "official-surface-release"
            (modified / "manifest.json").write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.stage_brand(stage, modified, BRAND_PIN)

            modified_offers = Path(tmp) / "offers-forged"
            shutil.copytree(offers, modified_offers)
            forged_offer = json.loads((modified_offers / "manifest.json").read_text("utf-8"))
            forged_offer["paid_purchases_enabled"] = True
            (modified_offers / "manifest.json").write_text(json.dumps(forged_offer), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "pin"):
                build.load_reference_offers(modified_offers, OFFERS_PIN)

    def test_unattested_releases_cannot_enter_public_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(build.SiteError, "attested publisher"):
                build.build(Path(tmp) / "out", "0" * 40, Path(tmp),
                            Path(tmp) / "arbitrary-publications.json",
                            public_origin="https://ordax.com.br")

    def test_unauthorized_catalog_fails_closed(self):
        result = render_catalog({"releases": []})
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["releases"], [])
        with self.assertRaises(PublicReleaseCatalogError):
            render_catalog({"releases": [{"release_id": "0" * 40, "public_authorized": False}]})

    def test_published_release_links_have_unambiguous_root_paths(self):
        for value in ("/releases/ordax-1.0.img", "/downloads/x86_64/stable.iso",
                      "/compliance/source_bundle-1.0.tar.gz"):
            with self.subTest(value=value):
                self.assertTrue(_same_origin_path(value))
        for value in ("/", "//remote/path", "/../account/export",
                      "/releases/../account/export", "/releases/./x",
                      "/releases//x", r"/releases\\x",
                      "/releases/%2e%2e/secret", "/releases/%2fadmin",
                      "/releases/secret?key=1", "/releases/file#fragment",
                      "https://example.org/file", "/releases/white space"):
            with self.subTest(value=value):
                self.assertFalse(_same_origin_path(value))

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

    def test_verified_brand_favicon_is_added_once(self):
        routes = {record["path"]: record for record in load_routes()}
        html = '<html><head><title>Site</title><meta name="description" content="Portal"></head><body></body></html>'
        public = render_html(html, routes["/"], "https://ordax.com.br")
        self.assertEqual(public.count('rel="icon"'), 1)
        self.assertIn('href="/assets/ordax-symbol.png"', public)
        existing = html.replace('</head>', '<link rel="icon" href="/assets/ordax-symbol.png" type="image/png"></head>')
        gated = render_html(existing, routes["/conta/"], "https://ordax.com.br")
        self.assertEqual(gated.count('rel="icon"'), 1)

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

    def test_surface_preview_is_single_pinned_artifact(self):
        source = ROOT / "artifacts/surface-preview/os-migration-70b0f7eb"
        self.assertTrue((source / "manifest.json").is_file())
        self.assertFalse((ROOT / "site/assets/playground-fixture.json").exists())
        self.assertFalse((ROOT / "site/assets/surface-snapshot.css").exists())
        self.assertFalse((ROOT / "site/assets/surface-snapshot.json").exists())
        self.assertEqual(
            build.digest((source / "manifest.json").read_bytes()),
            PREVIEW_PIN
        )
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            stage.mkdir()
            build.stage_brand(stage, ROOT / "artifacts/brand/os-migration-70b0f7eb", BRAND_PIN)
            receipt = build.stage_surface_preview(stage, source, build.digest((source / "manifest.json").read_bytes()))
            self.assertEqual(receipt["file_count"], 2)
            self.assertEqual(receipt["source_repository"], "ordaxsystems/ordax-os")
            self.assertTrue(receipt["font_url_rebased"])
            css = (stage / "assets/surface-snapshot.css").read_text("utf-8")
            self.assertIn("/assets/fonts/inter-latin-wght-normal.woff2", css)
            self.assertNotIn("/assets/inter-latin-wght-normal-Dx4kXJAl.woff2", css)
            self.assertFalse((stage / "assets/surface-snapshot.json").exists())
            with self.assertRaises(build.SiteError):
                build.stage_surface_preview(Path(tmp) / "unused", source, "0" * 64)

            altered = Path(tmp) / "altered"
            shutil.copytree(source, altered)
            fixture = altered / "assets/playground-fixture.json"
            fixture.write_bytes(fixture.read_bytes() + b" ")
            with self.assertRaises(build.SiteError):
                build.stage_surface_preview(Path(tmp) / "unused", altered, build.digest((altered / "manifest.json").read_bytes()))

    def test_delivered_css_dependencies_must_be_local_and_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            css_dir = bundle / "assets"
            css_dir.mkdir()
            (css_dir / "font.woff2").write_bytes(b"local-font")
            sheet = css_dir / "site.css"
            sheet.write_text('a{background:url("./font.woff2")} b{background:url(data:image/svg+xml,%3csvg%3e)}')
            self.assertEqual(check_css_dependencies(bundle), 1)
            for malicious in (
                "https://tracker.example/remote.png",
                "//tracker.example/remote.png",
                "../missing.png",
                "/assets/never-published.woff2",
                "/assets/../private.png",
            ):
                with self.subTest(malicious=malicious):
                    sheet.write_text('a{background:url("' + malicious + '")}')
                    with self.assertRaises(AssertionError):
                        check_css_dependencies(bundle)
            sheet.write_text('@import url("https://tracker.example/x.css");')
            with self.assertRaisesRegex(AssertionError, "import"):
                check_css_dependencies(bundle)

    def test_account_fallback_heading_is_not_a_second_runtime_heading(self):
        markup = (ROOT / "site/conta/index.html").read_text(encoding="utf-8")
        self.assertEqual(markup.count("<h1"), 1)
        self.assertIn('<h1 class="sr-only">Minha Conta OrdaX</h1>', markup)
        runtime = (ROOT / "site/assets/account-portal.js").read_text(encoding="utf-8")
        self.assertIn('document.getElementById("account-session").innerHTML', runtime)
        self.assertIn('document.getElementById("account-content").innerHTML', runtime)

    def test_site_is_not_native_web_surface(self):
        paths = (ROOT / "site").rglob("*")
        self.assertFalse(any("node_modules" in x.parts or ".env.production" in x.parts for x in paths))
        self.assertFalse((ROOT / "site/system").exists())
        self.assertFalse((ROOT / "site/tools/surface-web").exists())

if __name__ == "__main__":
    unittest.main()
