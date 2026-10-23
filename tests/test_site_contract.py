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

    def test_site_is_not_native_web_surface(self):
        paths = (ROOT / "site").rglob("*")
        self.assertFalse(any("node_modules" in x.parts or ".env.production" in x.parts for x in paths))
        self.assertFalse((ROOT / "site/system").exists())
        self.assertFalse((ROOT / "site/tools/surface-web").exists())

if __name__ == "__main__":
    unittest.main()
