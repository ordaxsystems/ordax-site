#!/usr/bin/env python3
"""Independent, fail-closed public-site candidate builder. No OS or Surface source imports."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from public_html_render import render_public_html
from public_release_catalog import render_catalog, validate_catalog
from site_routes import ROUTES, ROUTE_RECORDS
from site_seo import validate_origin, render_html, write_robots_sitemap

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BINARY_PROVENANCE = {
    "assets/account-landscape.jpg": "260e215794a3a38b03d0df6ce9395632aa7b78be",
    "assets/aurora-titanium.png": "e4574877f57a66574d001ebcfbfc8718782a2c23",
    "assets/download-hero.png": "7c23ed6070890d81a11474108f0a52a0965ce501",
    "assets/public-space-city.jpg": "189b498cf95572b45ccbbdc23ebc4eda9a66f257",
    "assets/public-surface-day.jpg": "9ae4fb9586e7c4267087c0bcba00b1f466f3866b",
    "assets/public-surface-night.jpg": "75f905b78bde6287a8a11c4062ef00ad1e469486",
}
BRAND_FILES = {
    "assets/ordax-design-tokens.css", "assets/ordax-font.css",
    "assets/ordax-symbol.png", "assets/ordax-landscape.png",
    "assets/fonts/inter-latin-wght-normal.woff2",
    "assets/fonts/Inter-OFL-1.1.txt",
}
REMOTE_SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
SCHEMA = "prototype-ordax.independent-public-site-bundle/1"
MAX_BUNDLE_FILES = 500
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
PREVIEW_FILES = {"assets/playground-fixture.json", "assets/surface-snapshot.css"}
PREVIEW_SCHEMA = "prototype-ordax.public-playground-fixture/1"
MIGRATION_LOCK_SCHEMA = "ordax.site-migration-artifact-lock/1"
MIGRATION_OWNER = "ordaxsystems/ordax-os"
MIGRATION_STATUS = "development-only-not-authorized-for-production"

class SiteError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate_bundle_inventory(ledger: dict) -> dict[str, dict]:
    """One canonical file inventory validator for local verify and staging.

    Manifests do not authorize publication; they enumerate candidate bytes.
    """
    records = ledger.get("files")
    if not isinstance(records, list) or not records or len(records) > MAX_BUNDLE_FILES:
        raise SiteError("site-bundle-file-inventory-invalid")
    files: dict[str, dict] = {}
    total_bytes = 0
    for row in records:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "size", "sha256"}
            or not isinstance(row["path"], str)
            or re.fullmatch(r"[A-Za-z0-9._/-]+", row["path"]) is None
            or row["path"].startswith("/")
            or any(part in ("", ".", "..") for part in row["path"].split("/"))
            or row["path"] == "public-site-manifest.json"
            or not isinstance(row["size"], int) or isinstance(row["size"], bool)
            or row["size"] < 0
            or not isinstance(row["sha256"], str)
            or SHA256.fullmatch(row["sha256"]) is None
            or row["path"] in files
        ):
            raise SiteError("site-bundle-file-inventory-invalid")
        total_bytes += row["size"]
        if total_bytes > MAX_BUNDLE_BYTES:
            raise SiteError("site-bundle-file-inventory-too-large")
        files[row["path"]] = row
    for required in ("config/public-site.json", "releases/catalog.json"):
        if required not in files:
            raise SiteError("site-bundle-file-inventory-missing:" + required)
    # No file may simultaneously act as the parent of another file.
    for name in files:
        parts = name.split("/")
        if any("/".join(parts[:i]) in files for i in range(1, len(parts))):
            raise SiteError("site-bundle-file-inventory-invalid")
    return files


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def safe_relative(value: object) -> bool:
    return (isinstance(value, str) and value.startswith("/")
            and not value.startswith("//") and "\\" not in value
            and "?" not in value and "#" not in value
            and ".." not in value.split("/"))

def check_source(strict_assets: bool = False) -> dict:
    if not SOURCE.is_dir():
        raise SiteError("missing site/ source")
    files = sorted(p for p in SOURCE.rglob("*") if p.is_file() or p.is_symlink())
    if any(p.is_symlink() for p in files):
        raise SiteError("symbolic links forbidden in site source")
    paths = {p.relative_to(SOURCE).as_posix() for p in files}
    missing_routes = set(ROUTES) - paths
    if paths.intersection(PREVIEW_FILES | {"assets/surface-snapshot.json"}):
        raise SiteError("generated Surface preview must come only from a pinned external artifact")
    if missing_routes:
        raise SiteError("missing routes: " + ", ".join(sorted(missing_routes)))
    config = json.loads((SOURCE / "config/public-site.json").read_text("utf-8"))
    if config.get("$schema") != "prototype-ordax.public-site-runtime/1":
        raise SiteError("runtime config schema mismatch")
    if config.get("product", {}).get("web", {}).get("enabled") is not False:
        raise SiteError("product Web may not be activated by the site")
    identity = config["identity"]
    for key in ("login_url", "register_url", "recovery_url", "recovery_complete_url"):
        if identity.get(key) is not None and not safe_relative(identity[key]):
            raise SiteError("unsafe identity target: " + key)
    if config["legal"].get("account_activation_ready") is not False:
        raise SiteError("source alone must not activate public account")
    if config["downloads"].get("catalog_url") != "/releases/catalog.json":
        raise SiteError("download catalog must be same-origin and versioned")
    for p in files:
        if p.suffix.lower() in {".js", ".css", ".html"}:
            value = p.read_text("utf-8")
            if p.suffix.lower() == ".js" and re.search(r"(?:import|from|require\().{0,120}system/surface/", value):
                raise SiteError("site imports internal Surface source: " + str(p))
            if "http://" in value or "https://" in value:
                scrubbed = value.replace(REMOTE_SCRIPT, "")
                scrubbed = re.sub(r'href="https://web\.ordax\.com\.br/"', 'href="/"', scrubbed)
                if "http://" in scrubbed or "https://" in scrubbed:
                    raise SiteError("unapproved external runtime reference: " + str(p))
    missing_binary = []
    for relative, sha in BINARY_PROVENANCE.items():
        path = SOURCE / relative
        if not path.is_file():
            missing_binary.append(relative)
        elif git_blob(path.read_bytes()) != sha:
            raise SiteError("binary source provenance mismatch: " + relative)
    if strict_assets and missing_binary:
        raise SiteError("missing original source assets: " + ", ".join(missing_binary))
    return {"source_files": len(files), "missing_source_assets": missing_binary}

def load_migration_lock(path: Path) -> dict:
    """Only the authored lock supplies hashes for the three dev-only artifacts."""
    if path.is_symlink() or not path.is_file():
        raise SiteError("migration artifact lock missing or symlinked")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (set(data) != {"$schema", "status", "source_repository", "source_commit", "artifacts"}
            or data["$schema"] != MIGRATION_LOCK_SCHEMA
            or data["status"] != MIGRATION_STATUS
            or data["source_repository"] != MIGRATION_OWNER
            or not SHA40.fullmatch(str(data["source_commit"]))
            or not isinstance(data["artifacts"], dict)
            or set(data["artifacts"]) != {"brand", "surface_preview", "offers"}):
        raise SiteError("invalid Site migration artifact trust lock")
    result = {}
    for key in ("brand", "surface_preview", "offers"):
        item = data["artifacts"][key]
        if not isinstance(item, dict) or set(item) != {"directory", "manifest_sha256"}:
            raise SiteError("invalid migration artifact lock item: " + key)
        relative = item["directory"]
        expected_prefix = {
            "brand": "artifacts/brand/",
            "surface_preview": "artifacts/surface-preview/",
            "offers": "artifacts/offers/",
        }[key]
        if (not isinstance(relative, str)
                or not relative.startswith(expected_prefix)
                or not re.fullmatch(r"[a-zA-Z0-9/_-]+", relative)
                or ".." in relative.split("/")
                or not SHA256.fullmatch(str(item["manifest_sha256"]))):
            raise SiteError("untrusted migration artifact lock path/digest: " + key)
        directory = ROOT / relative
        if directory.is_symlink() or not directory.is_dir():
            raise SiteError("missing or linked migration artifact: " + key)
        manifest, _ = load_pinned_manifest(directory, item["manifest_sha256"], key)
        if manifest.get("source_repository") != MIGRATION_OWNER or manifest.get("source_commit") != data["source_commit"]:
            raise SiteError("migration artifact diverges from common OS source revision: " + key)
        result[key] = {"directory": directory, "manifest_sha256": item["manifest_sha256"]}
    return result


def load_pinned_manifest(directory: Path, expected_sha256: str | None, label: str) -> tuple[dict, str]:
    """Verify trust anchor outside the manifest before interpreting any manifest claims."""
    if not SHA256.fullmatch(str(expected_sha256)):
        raise SiteError(label + " manifest SHA-256 pin is mandatory")
    path = directory / "manifest.json"
    if path.is_symlink() or not path.is_file():
        raise SiteError(label + " manifest missing or symlinked")
    payload = path.read_bytes()
    if digest(payload) != expected_sha256:
        raise SiteError(label + " manifest pin mismatch")
    return json.loads(payload), expected_sha256


def stage_brand(stage: Path, brand_dir: Path, expected_sha256: str | None) -> dict:
    ledger, pinned_sha256 = load_pinned_manifest(brand_dir, expected_sha256, "brand")
    if (ledger.get("artifact_class") != "ordax-brand"
            or ledger.get("source_repository") != "ordaxsystems/ordax-os"
            or ledger.get("status") != "audited-migration-snapshot-not-official-surface-publication"
            or ledger.get("immutable") is not True
            or not SHA40.fullmatch(str(ledger.get("source_commit", "")))):
        raise SiteError("unversioned/misidentified or falsely official brand artifact")
    if {r.get("path") for r in ledger.get("files", [])} != BRAND_FILES:
        raise SiteError("brand artifact file set mismatch")
    for row in ledger["files"]:
        name = row["path"]
        source = brand_dir / name
        if source.is_symlink() or not source.is_file() or not SHA256.fullmatch(str(row.get("sha256", ""))):
            raise SiteError("invalid brand artifact file")
        payload = source.read_bytes()
        if digest(payload) != row["sha256"] or len(payload) != row["size"]:
            raise SiteError("brand artifact integrity mismatch: " + name)
        target = stage / name
        if target.exists():
            raise SiteError("brand file conflicts with site-owned source: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return {"source_repository": ledger["source_repository"],
            "source_commit": ledger["source_commit"], "status": ledger["status"],
            "manifest_sha256": pinned_sha256}

def stage_surface_preview(stage: Path, directory: Path, expected_manifest_sha256: str) -> dict:
    """Stage the pinned presentation-only migration package, never source code."""
    manifest, _ = load_pinned_manifest(directory, expected_manifest_sha256, "Surface preview")
    if (manifest.get("artifact_class") != "ordax-public-surface-preview"
            or manifest.get("status") != "audited-migration-snapshot-not-official-surface-publication"
            or manifest.get("source_repository") != "ordaxsystems/ordax-os"
            or not SHA40.fullmatch(str(manifest.get("source_commit", "")))
            or manifest.get("immutable") is not True):
        raise SiteError("unverified, misidentified or falsely official Surface preview")
    files = manifest.get("files")
    if not isinstance(files, list) or {row.get("path") for row in files if isinstance(row, dict)} != PREVIEW_FILES or len(files) != len(PREVIEW_FILES):
        raise SiteError("Surface preview file inventory must be exact")
    payloads = {}
    for item in files:
        name = item["path"]
        src = directory / name
        if (src.is_symlink() or not src.is_file()
                or not SHA256.fullmatch(str(item.get("sha256", "")))
                or not SHA40.fullmatch(str(item.get("git_sha", "")))):
            raise SiteError("invalid Surface preview asset: " + name)
        value = src.read_bytes()
        if (digest(value) != item["sha256"] or len(value) != item.get("size")
                or git_blob(value) != item["git_sha"]):
            raise SiteError("Surface preview source integrity mismatch: " + name)
        payloads[name] = value
    fixture = json.loads(payloads["assets/playground-fixture.json"])
    if (fixture.get("$schema") != PREVIEW_SCHEMA
            or not isinstance(fixture.get("apps"), list)
            or not isinstance(fixture.get("home", {}).get("rail_apps"), list)
            or not isinstance(fixture.get("surface", {}).get("chrome"), str)
            or not isinstance(fixture.get("surface", {}).get("views", {}).get("home"), str)
            or fixture["surface"].get("cssSha256") != digest(payloads["assets/surface-snapshot.css"])):
        raise SiteError("Surface preview fixture/CSS composition mismatch")
    # Source CSS is immutable. Its historical Vite font URL is not exported
    # by the public Site. Repoint the staged view to the same Inter font from
    # the separately verified brand artifact, and hash the delivered CSS.
    source_font = b"url(/assets/inter-latin-wght-normal-Dx4kXJAl.woff2)"
    delivered_font = b"url(/assets/fonts/inter-latin-wght-normal.woff2)"
    css = payloads["assets/surface-snapshot.css"]
    font_rebased = source_font in css
    if font_rebased:
        if not (stage / "assets/fonts/inter-latin-wght-normal.woff2").is_file():
            raise SiteError("preview font depends on missing verified brand")
        css = css.replace(source_font, delivered_font)
    for target in re.findall(rb"url\((/assets/[A-Za-z0-9./_-]+)\)", css):
        referenced = stage / target.decode("ascii").lstrip("/")
        if target != b"/assets/surface-snapshot.css" and not referenced.is_file():
            raise SiteError("preview CSS references a missing same-origin asset: " + target.decode("ascii"))
    payloads["assets/surface-snapshot.css"] = css
    for name, value in payloads.items():
        dest = stage / name
        if dest.exists():
            raise SiteError("Site duplicates Surface-owned preview: " + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(value)
    return {"source_repository": manifest["source_repository"],
            "source_commit": manifest["source_commit"],
            "manifest_sha256": expected_manifest_sha256,
            "status": manifest["status"],
            "file_count": len(PREVIEW_FILES),
            "rendered_css_sha256": digest(css), "font_url_rebased": font_rebased}


def load_reference_offers(directory: Path | None, expected_sha256: str | None) -> tuple[str, dict | None]:
    if directory is None:
        if expected_sha256 is not None:
            raise SiteError("offers manifest pin without an artifact")
        # No official presentation projection supplied: reference offers stay unavailable.
        return '<p class="commercial-notice">Catálogo de planos em preparação.</p>', None
    manifest, pinned_sha256 = load_pinned_manifest(directory, expected_sha256, "offers")
    if (manifest.get("artifact_class") != "ordax-public-reference-offers"
            or manifest.get("source_repository") != "ordaxsystems/ordax-os"
            or manifest.get("status") != "reference-not-purchasable"
            or not SHA40.fullmatch(str(manifest.get("source_commit", "")))
            or manifest.get("paid_purchases_enabled") is not False
            or manifest.get("commercial_capacity_allocation_enabled") is not False
            or manifest.get("html_path") != "reference-offers.html"):
        raise SiteError("reference offers are unapproved or incorrectly identified")
    path = directory / "reference-offers.html"
    if not path.is_file() or path.is_symlink():
        raise SiteError("reference offers artifact missing or linked")
    payload = path.read_bytes()
    if (not SHA256.fullmatch(str(manifest.get("html_sha256", "")))
            or digest(payload) != manifest["html_sha256"]
            or len(payload) != manifest.get("html_size")):
        raise SiteError("reference offers integrity mismatch")
    html = payload.decode("utf-8")
    if (not html.startswith('<div class="commercial-catalog">')
            or "Planos em preparação" not in html
            or "contratação indisponível" not in html
            or re.search(r"<\s*(?:script|form|iframe|a)\b", html, re.I)
            or re.search(r"\b(?:href|action|on[a-z]+)\s*=", html, re.I)):
        raise SiteError("reference offers contain interactive, unavailable or untrusted content")
    return html, {"source_repository": manifest["source_repository"],
                  "source_commit": manifest["source_commit"],
                  "status": manifest["status"],
                  "manifest_sha256": pinned_sha256}


def build(out: Path, sha: str, brand: Path, publications: Path | None,
          offers_dir: Path | None = None, public_origin: str | None = None,
          surface_preview_dir: Path | None = None,
          surface_preview_manifest_sha256: str | None = None,
          brand_manifest_sha256: str | None = None,
          offers_manifest_sha256: str | None = None) -> dict:
    if not SHA40.fullmatch(sha):
        raise SiteError("full Git SHA required")
    origin = validate_origin(public_origin)
    # A boolean "public_authorized" in an arbitrary local JSON file is not
    # publisher attestation. No official release artifact trust policy exists.
    # Keep the download catalog empty until an explicitly authenticated
    # publishing handoff can be implemented; preserve only the offline renderer.
    if publications is not None:
        raise SiteError("public downloads require an attested publisher artifact; local --publications is forbidden")
    check_source(strict_assets=True)
    if out.exists():
        raise SiteError("refusing to replace existing build output")
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".ordax-site-", dir=out.parent))
    try:
        shutil.copytree(SOURCE, temp, dirs_exist_ok=True)
        brand_receipt = stage_brand(temp, brand, brand_manifest_sha256)
        if surface_preview_dir is None:
            raise SiteError("Surface preview artifact required; no embedded Surface copy")
        preview_receipt = stage_surface_preview(
            temp, surface_preview_dir, surface_preview_manifest_sha256 or ""
        )
        offers_html, offers_receipt = load_reference_offers(offers_dir, offers_manifest_sha256)
        route_by_source = {item["source"]: item for item in ROUTE_RECORDS}
        for page in temp.rglob("*.html"):
            relative = page.relative_to(temp).as_posix()
            if relative not in route_by_source:
                raise SiteError("HTML page has no declared route: " + relative)
            markup = render_public_html(page.read_text("utf-8"))
            for marker, expected in (
                ("<!-- ORDAX_PUBLIC_PLAN_CATALOG -->", "index.html"),
                ("<!-- ORDAX_ACCOUNT_PLAN_CATALOG -->", "conta/index.html"),
            ):
                if marker in markup:
                    if page.relative_to(temp).as_posix() != expected or markup.count(marker) != 1:
                        raise SiteError("offers catalog marker outside its official presentation page")
                    markup = markup.replace(marker, offers_html)
            # CSS source receipts stay immutable; the query tracks the bytes
            # actually distributed after verified font URL rebasing.
            markup = re.sub(r"(/assets/surface-snapshot\.css\?v=)[0-9a-f]{12}",
                            lambda match: match.group(1) + preview_receipt["rendered_css_sha256"][:12], markup)
            page.write_text(render_html(markup, route_by_source[relative], origin), encoding="utf-8")
        write_robots_sitemap(temp, origin)
        # The Site cannot authorize releases. Without independently attested
        # public-publisher input, the only safe downloadable catalog is empty.
        catalog = render_catalog({"releases": []})
        publications_digest = None
        dest = temp / "releases/catalog.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validate_catalog(dest)
        records = [
            {"path": p.relative_to(temp).as_posix(), "sha256": digest(p.read_bytes()), "size": p.stat().st_size}
            for p in sorted(temp.rglob("*")) if p.is_file()
        ]
        manifest = {"$schema": SCHEMA, "source_commit": sha, "artifact_class": "public-site",
                    "brand": brand_receipt, "surface_preview": preview_receipt,
                    "offers": offers_receipt, "publications_sha256": publications_digest,
                    "seo_origin": origin, "indexable_routes": [row["path"] for row in ROUTE_RECORDS if row["indexable"]],
                    "catalog_status": catalog["status"], "files": records}
        (temp / "public-site-manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, out)
        temp = None
        return manifest
    finally:
        if temp is not None:
            shutil.rmtree(temp, ignore_errors=True)

def verify(out: Path) -> None:
    ledger = json.loads((out / "public-site-manifest.json").read_text("utf-8"))
    if ledger.get("$schema") != SCHEMA or not SHA40.fullmatch(str(ledger.get("source_commit", ""))):
        raise SiteError("bundle identity invalid")
    if ledger.get("artifact_class") != "public-site":
        raise SiteError("bundle identity invalid")
    expected = validate_bundle_inventory(ledger)
    paths = list(out.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise SiteError("bundle contains symbolic links")
    files = {p.relative_to(out).as_posix(): p for p in paths if p.is_file()}
    if set(files) != set(expected) | {"public-site-manifest.json"}:
        raise SiteError("bundle path inventory mismatch")
    for relative, row in expected.items():
        path = files[relative]
        raw = path.read_bytes()
        if len(raw) != row["size"] or digest(raw) != row["sha256"]:
            raise SiteError("bundle integrity mismatch: " + relative)
    catalog = validate_catalog(out / "releases/catalog.json")
    # The existing Site bundle manifest is the build's publication-state
    # record. Reject a valid but swapped catalog or a forged "ready" marker.
    if ledger.get("catalog_status") != catalog["status"]:
        raise SiteError("bundle publication state mismatch")
    publication_digest = ledger.get("publications_sha256")
    if catalog["status"] == "empty":
        if publication_digest is not None:
            raise SiteError("empty catalog cannot have a publisher receipt")
    elif not isinstance(publication_digest, str) or not SHA256.fullmatch(publication_digest):
        raise SiteError("ready catalog requires an attested publisher receipt")

def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("command", choices=("check", "build", "verify"))
    cli.add_argument("--source-commit")
    cli.add_argument("--brand-dir")
    cli.add_argument("--brand-manifest-sha256")
    cli.add_argument("--publications")
    cli.add_argument("--migration-lock")
    cli.add_argument("--offers-dir")
    cli.add_argument("--offers-manifest-sha256")
    cli.add_argument("--public-origin")
    cli.add_argument("--surface-preview-dir")
    cli.add_argument("--surface-preview-manifest-sha256")
    cli.add_argument("--out", default="out/site")
    args = cli.parse_args()
    if args.command == "check":
        report = check_source()
        print(json.dumps({"structural_check": "PASS", **report}, sort_keys=True))
    elif args.command == "build":
        brand = Path(args.brand_dir) if args.brand_dir else None
        brand_hash = args.brand_manifest_sha256
        preview = Path(args.surface_preview_dir) if args.surface_preview_dir else None
        preview_hash = args.surface_preview_manifest_sha256
        offers = Path(args.offers_dir) if args.offers_dir else None
        offers_hash = args.offers_manifest_sha256
        if args.migration_lock:
            if any(x is not None for x in (brand, brand_hash, preview, preview_hash, offers, offers_hash)):
                raise SiteError("migration lock and individual artifact overrides are mutually exclusive")
            pinned = load_migration_lock(Path(args.migration_lock))
            brand = pinned["brand"]["directory"]
            brand_hash = pinned["brand"]["manifest_sha256"]
            preview = pinned["surface_preview"]["directory"]
            preview_hash = pinned["surface_preview"]["manifest_sha256"]
            offers = pinned["offers"]["directory"]
            offers_hash = pinned["offers"]["manifest_sha256"]
        if brand is None:
            raise SiteError("brand artifact required (pinned manifest + SHA-256); no OS source fallback")
        print(json.dumps(build(Path(args.out), args.source_commit or "", brand,
                               Path(args.publications) if args.publications else None,
                               offers,
                               args.public_origin,
                               preview,
                               preview_hash,
                               brand_hash,
                               offers_hash), sort_keys=True))
    else:
        verify(Path(args.out))
        print("SITE_BUNDLE_VERIFY=PASS")

if __name__ == "__main__":
    try:
        main()
    except (SiteError, ValueError, OSError) as error:
        raise SystemExit(f"SITE_ERROR: {error}")
