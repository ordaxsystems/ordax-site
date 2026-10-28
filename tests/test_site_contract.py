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
from public_release_catalog import render_catalog, validate_catalog, PublicReleaseCatalogError, _same_origin_path
from site_routes import load_routes
from site_seo import validate_origin, render_html
from smoke_static import check_css_dependencies

DEV_LOCK = build.load_dev_artifact_lock(ROOT / "contracts/dev-artifact-lock.json")
BRAND_PIN = DEV_LOCK["brand"]["manifest_sha256"]
PREVIEW_PIN = DEV_LOCK["surface_preview"]["manifest_sha256"]

class SiteContractTests(unittest.TestCase):
    def test_owner_and_routes(self):
        report = build.check_source(strict_assets=False)
        self.assertGreater(report["source_files"], 25)
        self.assertEqual(len(build.ROUTES), 11)
        self.assertEqual(len(set(build.ROUTES)), len(build.ROUTES))

    def test_identity_and_mcp_account_data_share_bounded_json_transport(self):
        shell = (ROOT / "site/assets/site.js").read_text(encoding="utf-8")
        portal = (ROOT / "site/assets/account-portal.js").read_text(encoding="utf-8")
        self.assertIn("const MAX_PUBLIC_JSON_BYTES = 256 * 1024", shell)
        self.assertIn("async function readJsonBytes(response", shell)
        self.assertIn('return parseJsonBytes(await readJsonBytes(response))', shell)
        self.assertIn('const payload = await loadJson("/account/usage/mcp", signal)', shell)
        self.assertIn('owner !== sessionView', shell)
        self.assertIn('if (mcpUsageSession !== session)', portal)
        self.assertNotIn('session.email || "verified-session"', portal)
        self.assertIn('const bytes = await readJsonBytes(response, record.size)', shell)
        self.assertIn("account.readMcpUsage(signal)", portal)
        self.assertNotIn('fetch("/account/usage/mcp"', portal)
        self.assertNotIn("response.json()", portal)

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

    def test_development_lock_accepts_only_owner_releases(self):
        self.assertEqual(set(DEV_LOCK), {"brand", "surface_preview"})
        pin = DEV_LOCK["brand"]["release"]
        self.assertEqual(pin["source_repository"], "ordaxsystems/ordax-surface")
        self.assertEqual(pin["release_tag"], "brand-dev-" + pin["source_commit"])
        self.assertRegex(pin["archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(pin["manifest_sha256"], BRAND_PIN)
        self.assertFalse((ROOT / "artifacts/brand/os-migration-70b0f7eb").exists())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.json"
            original = json.loads((ROOT / "contracts/dev-artifact-lock.json").read_text("utf-8"))
            original["status"] = "official"
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "lock"):
                build.load_dev_artifact_lock(path)
            original["status"] = build.DEV_ARTIFACT_STATUS
            original["artifacts"]["brand"]["release"]["release_tag"] = "brand-dev-main"
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "signed Dev release"):
                build.load_dev_artifact_lock(path)

    def test_active_operational_docs_use_only_current_signed_dev_artifacts(self):
        """Retired migration inputs must not return via published runbooks."""
        docs = ("README.md", "AGENTS.md", "docs/ACCESSIBILITY-GATES.md")
        for name in docs:
            with self.subTest(document=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("contracts/dev-artifact-lock.json", content)
                self.assertNotIn("contracts/migration-artifact-lock.json", content)
                self.assertNotIn("--migration-lock", content)
        self.assertFalse((ROOT / "contracts/migration-artifact-lock.json").exists())
        self.assertEqual(set(DEV_LOCK), {"brand", "surface_preview"})
        deployment = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertIn("--dev-lock contracts/dev-artifact-lock.json",
                      deployment["buildCommand"])

    def test_site_inactive_plans_do_not_duplicate_os_entitlements(self):
        self.assertFalse((ROOT / "artifacts/offers/os-migration-70b0f7eb").exists())
        self.assertNotIn("offers", DEV_LOCK)
        self.assertIn("Planos em preparação", build.INACTIVE_PLANS_HTML)
        self.assertIn("contratação indisponível", build.INACTIVE_PLANS_HTML)
        self.assertNotIn("commercial-plan", build.INACTIVE_PLANS_HTML)

    def test_unattested_releases_cannot_enter_public_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(build.SiteError, "attested publisher"):
                build.build(Path(tmp) / "out", "0" * 40, Path(tmp),
                            Path(tmp) / "arbitrary-publications.json",
                            public_origin="https://ordax.com.br")

    def test_bundle_publication_state_is_not_a_self_authorization_flag(self):
        # Tiny self-contained bundle proves the verifier uses the already
        # canonical manifest, without staging Surface or calling any backend.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            artifact = out / "releases/catalog.json"
            artifact.parent.mkdir()
            artifact.write_text(json.dumps(render_catalog({"releases": []})), encoding="utf-8")
            config = out / "config/public-site.json"
            config.parent.mkdir()
            config.write_text('{"$schema":"prototype-ordax.public-site-runtime/1"}', encoding="utf-8")
            ledger = {
                "$schema": build.SCHEMA, "source_commit": "1" * 40,
                "artifact_class": "public-site",
                "catalog_status": "empty", "publications_sha256": None,
                "files": [
                    {"path": entry.relative_to(out).as_posix(),
                     "size": entry.stat().st_size,
                     "sha256": build.digest(entry.read_bytes())}
                    for entry in (artifact, config)
                ],
            }
            manifest = out / "public-site-manifest.json"

            def verify_with(**fields):
                manifest.write_text(json.dumps({**ledger, **fields}), encoding="utf-8")
                build.verify(out)

            verify_with()
            with self.assertRaisesRegex(build.SiteError, "publication state mismatch"):
                verify_with(catalog_status="ready")
            with self.assertRaisesRegex(build.SiteError, "empty catalog cannot have"):
                verify_with(publications_sha256="f" * 64)
            with self.assertRaisesRegex(build.SiteError, "publication state mismatch"):
                verify_with(catalog_status="missing")

    def test_build_and_staging_share_one_strict_bundle_inventory_contract(self):
        records = [
            {"path": "config/public-site.json", "size": 12, "sha256": "a" * 64},
            {"path": "releases/catalog.json", "size": 0, "sha256": "b" * 64},
            {"path": "login/index.html", "size": 24, "sha256": "c" * 64},
        ]
        manifest = {"files": records}
        self.assertEqual(set(build.validate_bundle_inventory(manifest)),
                         {row["path"] for row in records})
        for modification in (
            lambda v: v["files"].append(dict(v["files"][0])),
            lambda v: v["files"][0].update({"path": "login/../index.html"}),
            lambda v: v["files"][0].update({"path": "public-site-manifest.json"}),
            lambda v: v["files"][0].update({"size": True}),
            lambda v: v["files"][0].update({"sha256": "not-hash"}),
            lambda v: v["files"].append({"path": "login", "size": 1, "sha256": "d" * 64}),
            lambda v: v["files"].pop(0),
            lambda v: v["files"][0].update({"size": build.MAX_BUNDLE_BYTES + 1}),
        ):
            import copy
            bad = copy.deepcopy(manifest)
            modification(bad)
            with self.subTest(bad=bad), self.assertRaises(build.SiteError):
                build.validate_bundle_inventory(bad)

    def test_self_attested_ready_catalog_is_rejected_even_if_bundle_bytes_match(self):
        # Do not mistake manifest integrity for publisher authority. Simulate
        # a valid release and a matching altered manifest entirely offline.
        asset = lambda href: {"href": href, "sha256": "a" * 64, "size": 123}
        commit = "1" * 40
        published = render_catalog({"releases": [{
            "release_id": commit, "source_commit": commit,
            "version": "offline-test", "channel": "test",
            "published_at": "2026-10-24", "public_authorized": True,
            "targets": [{"id": "test-image", "label": "Test", **asset("/test.img"),
                         "public_download_authorized": True}],
            "compliance": {"public_compliance_authorized": True,
                           "sbom": asset("/test-sbom.json"),
                           "third_party_notices": asset("/test-notices.txt"),
                           "source_bundle": asset("/test-source.tar.gz")},
        }]})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            catalog = out / "releases/catalog.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(json.dumps(published), encoding="utf-8")
            config = out / "config/public-site.json"
            config.parent.mkdir(parents=True)
            config.write_text('{"$schema":"prototype-ordax.public-site-runtime/1"}',
                              encoding="utf-8")
            manifest = {
                "$schema": build.SCHEMA, "artifact_class": "public-site",
                "source_commit": commit,
                "catalog_status": "ready", "publications_sha256": "a" * 64,
                "files": [{"path": p.relative_to(out).as_posix(),
                           "sha256": build.digest(p.read_bytes()),
                           "size": p.stat().st_size} for p in (config, catalog)],
            }
            (out / "public-site-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "independently attested publisher"):
                build.verify(out)

    def test_unauthorized_catalog_fails_closed(self):
        result = render_catalog({"releases": []})
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["releases"], [])
        with self.assertRaises(PublicReleaseCatalogError):
            render_catalog({"releases": [{"release_id": "0" * 40, "public_authorized": False}]})

    def test_distributed_ready_catalog_rejects_partial_or_duplicate_downloads(self):
        # Synthetic, never distributed publisher data; the real builder keeps
        # releases empty without an independently attested publisher handoff.
        asset = lambda href: {"href": href, "sha256": "a" * 64, "size": 123}
        target = {"id": "usb-amd64", "label": "Test target",
                  **asset("/downloads/test-only.img")}
        release_id = "1" * 40
        authorized_test_projection = render_catalog({"releases": [{
            "release_id": release_id,
            "source_commit": release_id,
            "version": "test-only",
            "channel": "test",
            "published_at": "2026-10-24",
            "public_authorized": True,
            "targets": [{**target, "public_download_authorized": True}],
            "compliance": {
                "public_compliance_authorized": True,
                "sbom": asset("/compliance/test-sbom.json"),
                "third_party_notices": asset("/compliance/test-notices.txt"),
                "source_bundle": asset("/compliance/test-sources.tar.gz"),
            },
        }]})
        import copy
        original = authorized_test_projection["releases"][0]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            def check(value):
                path.write_text(json.dumps(value), encoding="utf-8")
                return validate_catalog(path)
            self.assertEqual(check(authorized_test_projection), authorized_test_projection)

            for field in ("version", "channel", "published_at"):
                invalid = copy.deepcopy(authorized_test_projection)
                invalid["releases"][0][field] = "  "
                with self.subTest(field=field), self.assertRaisesRegex(
                    PublicReleaseCatalogError, field
                ):
                    check(invalid)

            invalid = copy.deepcopy(authorized_test_projection)
            invalid["releases"][0]["targets"].append(copy.deepcopy(
                invalid["releases"][0]["targets"][0]
            ))
            with self.assertRaisesRegex(PublicReleaseCatalogError, "duplicate target id"):
                check(invalid)

            invalid = copy.deepcopy(authorized_test_projection)
            invalid["releases"][0]["targets"][0]["href"] = "/downloads/%2e%2e/auth/login"
            with self.assertRaisesRegex(PublicReleaseCatalogError, "same-origin"):
                check(invalid)

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

    def test_surface_preview_is_one_pinned_external_release_without_legacy_copy(self):
        pin = DEV_LOCK["surface_preview"]["release"]
        self.assertEqual(pin["source_repository"], "ordaxsystems/ordax-surface")
        self.assertEqual(pin["release_tag"], "meridian-dev-" + pin["source_commit"])
        self.assertEqual(pin["manifest_sha256"], PREVIEW_PIN)
        self.assertRegex(pin["archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse((ROOT / "artifacts/surface-preview/os-migration-70b0f7eb").exists())
        self.assertFalse((ROOT / "site/assets/playground-fixture.json").exists())
        self.assertFalse((ROOT / "site/assets/surface-snapshot.css").exists())
        self.assertFalse((ROOT / "site/assets/surface-snapshot.json").exists())
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "forged-lock.json"
            lock = json.loads((ROOT / "contracts/dev-artifact-lock.json").read_text("utf-8"))
            lock["artifacts"]["surface_preview"]["release"]["release_tag"] = "meridian-dev-main"
            fake.write_text(json.dumps(lock), encoding="utf-8")
            with self.assertRaisesRegex(build.SiteError, "invalid signed Dev release lock"):
                build.load_dev_artifact_lock(fake)

    def test_retired_os_surface_preview_cannot_reenter_signed_dev_bundle(self):
        """Even a correctly hashed OS-era manifest must not be accepted."""
        source = (ROOT / "scripts/build.py").read_text(encoding="utf-8")
        self.assertNotIn("ordax-public-surface-preview", source)
        self.assertNotIn("audited-migration-snapshot-not-official-surface-publication", source)
        smoke_source = (ROOT / "scripts/smoke_static.py").read_text(encoding="utf-8")
        self.assertNotIn("audited-migration-snapshot-not-official-surface-publication", smoke_source)
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp) / "retired-os-preview"
            source_dir.mkdir()
            old_manifest = {
                "$schema": "prototype-ordax.public-surface-preview/1",
                "artifact_class": "ordax-public-surface-preview",
                "source_repository": "ordaxsystems/ordax-os",
                "source_commit": "1" * 40,
                "status": "audited-migration-snapshot-not-official-surface-publication",
                "immutable": True,
            }
            encoded = (json.dumps(old_manifest, sort_keys=True) + "\n").encode("utf-8")
            (source_dir / "manifest.json").write_bytes(encoded)
            digest = build.digest(encoded)
            out = Path(tmp) / "site-output"
            with self.assertRaisesRegex(build.SiteError, "retired OS Surface migration preview"):
                build.stage_surface_preview(out, source_dir, digest)
            self.assertFalse(out.exists())

    def test_verified_surface_images_reuse_site_bytes_without_duplicate_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            assets = stage / "assets"
            assets.mkdir()
            day, night = b"same-signed-image-day", b"same-signed-image-night"
            (assets / "public-surface-day.jpg").write_bytes(day)
            (assets / "public-surface-night.jpg").write_bytes(night)
            original_fixture = (b'{"html":"<img src=\\"/assets/alpine-day-Hash.jpg\\">",'
                                b'"alt":"/assets/alpine-night-Hash.jpg"}')
            payloads = {
                "assets/alpine-day-Hash.jpg": day,
                "assets/alpine-night-Hash.jpg": night,
                "assets/surface-snapshot.css": b"body{background:url(./alpine-night-Hash.jpg)}",
                "assets/playground-fixture.json": original_fixture,
            }
            self.assertEqual(build.coalesce_verified_site_images(stage, payloads), 2)
            self.assertNotIn("assets/alpine-day-Hash.jpg", payloads)
            self.assertNotIn("assets/alpine-night-Hash.jpg", payloads)
            self.assertIn(b"/assets/public-surface-day.jpg",
                          payloads["assets/playground-fixture.json"])
            self.assertIn(b"/assets/public-surface-night.jpg",
                          payloads["assets/playground-fixture.json"])
            self.assertIn(b"./public-surface-night.jpg",
                          payloads["assets/surface-snapshot.css"])
            self.assertEqual((assets / "public-surface-day.jpg").read_bytes(), day)
            self.assertEqual((assets / "public-surface-night.jpg").read_bytes(), night)
            # Same name / similar size alone cannot authorize deduplication.
            different = {"assets/alpine-day-Hash.jpg": b"changed-image"}
            self.assertEqual(build.coalesce_verified_site_images(stage, different), 0)
            self.assertIn("assets/alpine-day-Hash.jpg", different)
            # Do not remove a file when any source reference could become orphaned.
            unsafe = {"assets/alpine-day-Hash.jpg": day,
                      "assets/playground-fixture.json": b"url(alpine-day-Hash.jpg)"}
            with self.assertRaisesRegex(build.SiteError, "unmapped Surface image"):
                build.coalesce_verified_site_images(stage, unsafe)

    def test_bundle_verify_rejects_duplicate_binary_digest_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "assets").mkdir()
            (out / "config").mkdir()
            (out / "releases").mkdir()
            (out / "assets/one.jpg").write_bytes(b"duplicate-bytes")
            (out / "assets/two.jpg").write_bytes(b"duplicate-bytes")
            (out / "config/public-site.json").write_text("{}", encoding="utf-8")
            (out / "releases/catalog.json").write_text("{}", encoding="utf-8")
            manifest = {
                "$schema": build.SCHEMA, "source_commit": "1" * 40,
                "artifact_class": "public-site",
                "files": [
                    {"path": path.relative_to(out).as_posix(),
                     "sha256": build.digest(path.read_bytes()),
                     "size": path.stat().st_size}
                    for path in sorted(out.rglob("*")) if path.is_file()
                ],
            }
            (out / "public-site-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with self.assertRaisesRegex(build.SiteError,
                                        "duplicate distributed binary assets"):
                build.verify(out)

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

    def test_independent_vercel_host_preserves_owner_and_publication_gates(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(config["outputDirectory"], "out/site")
        self.assertEqual(config["framework"], None)
        self.assertIn("scripts/build.py build", config["buildCommand"])
        self.assertIn("--dev-lock contracts/dev-artifact-lock.json",
                      config["buildCommand"])
        self.assertIn("scripts/build.py verify", config["buildCommand"])
        self.assertNotIn("tools/public-site", config["buildCommand"])
        self.assertNotIn("ordax-os", config["buildCommand"])
        self.assertEqual(config["git"]["deploymentEnabled"], {"**": False, "main": True})
        # The only auth routes are same-origin transport into one pinned OS
        # gateway; no Site-owned Identity logic, bypass or public activation.
        self.assertEqual(config["rewrites"], [
            {"source": f"/{prefix}/:path*",
             "destination": f"/api/account-proxy?ordax_path=/{prefix}/:path*"}
            for prefix in ("auth", "sync", "account")
        ])
        self.assertIn("npm ci --omit=dev --ignore-scripts", config["installCommand"])
        self.assertIn("stage_canonical_gateway.py --out .gateway-source", config["installCommand"])
        adapter = (ROOT / "api/account-proxy.mjs").read_text(encoding="utf-8")
        self.assertIn('../.gateway-source/api/account-proxy.mjs', adapter)
        self.assertNotIn("jwtVerify", adapter)
        self.assertNotIn("createClient", adapter)
        self.assertEqual(
            json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["dependencies"],
            {"@vercel/oidc": "4.0.0"},
        )
        self.assertFalse((ROOT / ".env.production").exists())
        headers = config["headers"][0]["headers"]
        self.assertIn({"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}, headers)
        self.assertTrue(any(row["key"] == "Content-Security-Policy" for row in headers))

    def test_ci_candidate_comes_from_real_git_revision_once_per_pr(self):
        # Avoid building two different candidates for the same PR revision:
        # Actions defaults to an ephemeral merge SHA on pull_request events.
        workflow = (ROOT / ".github/workflows/site-source.yml").read_text("utf-8")
        self.assertIn("branches: [main]", workflow)
        self.assertNotIn("branches: [main, feat/site-independent-extraction]", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('--source-commit "$(git rev-parse HEAD)"', workflow)
        self.assertIn("SITE_CANDIDATE_SOURCE_COMMIT=", workflow)
        self.assertIn("SITE_CANDIDATE_MANIFEST_SHA256=", workflow)

    def test_site_is_not_native_web_surface(self):
        paths = (ROOT / "site").rglob("*")
        self.assertFalse(any("node_modules" in x.parts or ".env.production" in x.parts for x in paths))
        self.assertFalse((ROOT / "site/system").exists())
        self.assertFalse((ROOT / "site/tools/surface-web").exists())

if __name__ == "__main__":
    unittest.main()
