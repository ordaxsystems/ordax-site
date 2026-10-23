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
from public_release_catalog import load_publications, render_catalog, validate_catalog
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

class SiteError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

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

def stage_brand(stage: Path, brand_dir: Path) -> dict:
    ledger = json.loads((brand_dir / "manifest.json").read_text("utf-8"))
    if ledger.get("artifact_class") != "ordax-brand" or not SHA40.fullmatch(str(ledger.get("source_commit", ""))):
        raise SiteError("unversioned/untrusted brand artifact")
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
    return {"source_commit": ledger["source_commit"], "manifest_sha256": digest((brand_dir / "manifest.json").read_bytes())}

def load_reference_offers(directory: Path | None) -> tuple[str, dict | None]:
    if directory is None:
        # No official presentation projection supplied: reference offers stay unavailable.
        return '<p class="commercial-notice">Catálogo de planos em preparação.</p>', None
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("artifact_class") != "ordax-public-reference-offers"
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
    return html, {"source_commit": manifest["source_commit"],
                  "manifest_sha256": digest(manifest_path.read_bytes())}


def build(out: Path, sha: str, brand: Path, publications: Path | None,
          offers_dir: Path | None = None, public_origin: str | None = None) -> dict:
    if not SHA40.fullmatch(sha):
        raise SiteError("full Git SHA required")
    origin = validate_origin(public_origin)
    check_source(strict_assets=True)
    if out.exists():
        raise SiteError("refusing to replace existing build output")
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".ordax-site-", dir=out.parent))
    try:
        shutil.copytree(SOURCE, temp, dirs_exist_ok=True)
        brand_receipt = stage_brand(temp, brand)
        offers_html, offers_receipt = load_reference_offers(offers_dir)
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
            page.write_text(render_html(markup, route_by_source[relative], origin), encoding="utf-8")
        write_robots_sitemap(temp, origin)
        # Site does not authorize releases: a missing official publication produces
        # an empty catalog. The release owner must supply an explicit approved file.
        if publications is None:
            catalog = render_catalog({"releases": []})
            publications_digest = None
        else:
            canonical = load_publications(publications)
            catalog = render_catalog(canonical)
            publications_digest = digest(publications.read_bytes())
        dest = temp / "releases/catalog.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validate_catalog(dest)
        records = [
            {"path": p.relative_to(temp).as_posix(), "sha256": digest(p.read_bytes()), "size": p.stat().st_size}
            for p in sorted(temp.rglob("*")) if p.is_file()
        ]
        manifest = {"$schema": SCHEMA, "source_commit": sha, "artifact_class": "public-site",
                    "brand": brand_receipt, "offers": offers_receipt, "publications_sha256": publications_digest,
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
    expected = ledger.get("files", [])
    names = [r["path"] for r in expected]
    if len(names) != len(set(names)):
        raise SiteError("bundle contains duplicate paths")
    files = {p.relative_to(out).as_posix(): p for p in out.rglob("*") if p.is_file()}
    if set(files) != set(names) | {"public-site-manifest.json"}:
        raise SiteError("bundle path inventory mismatch")
    for row in expected:
        path = files[row["path"]]
        if path.is_symlink() or len(path.read_bytes()) != row["size"] or digest(path.read_bytes()) != row["sha256"]:
            raise SiteError("bundle integrity mismatch: " + row["path"])
    validate_catalog(out / "releases/catalog.json")

def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("command", choices=("check", "build", "verify"))
    cli.add_argument("--source-commit")
    cli.add_argument("--brand-dir")
    cli.add_argument("--publications")
    cli.add_argument("--offers-dir")
    cli.add_argument("--public-origin")
    cli.add_argument("--out", default="out/site")
    args = cli.parse_args()
    if args.command == "check":
        report = check_source()
        print(json.dumps({"structural_check": "PASS", **report}, sort_keys=True))
    elif args.command == "build":
        if not args.brand_dir:
            raise SystemExit("brand artifact required (pinned manifest + SHA-256); no OS source fallback")
        print(json.dumps(build(Path(args.out), args.source_commit or "", Path(args.brand_dir),
                               Path(args.publications) if args.publications else None,
                               Path(args.offers_dir) if args.offers_dir else None,
                               args.public_origin), sort_keys=True))
    else:
        verify(Path(args.out))
        print("SITE_BUNDLE_VERIFY=PASS")

if __name__ == "__main__":
    try:
        main()
    except (SiteError, ValueError, OSError) as error:
        raise SystemExit(f"SITE_ERROR: {error}")
