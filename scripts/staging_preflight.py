#!/usr/bin/env python3
"""Read-only, opt-in staging gateway preflight for an independent Site bundle.

No credentials, POST requests, cookies, login simulations, deployment or DNS
changes. Passing proves ONLY the anonymous response contracts at that origin,
not authenticated Identity, publishing authority, or production readiness.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import ssl
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener

from public_identity_state import PublicIdentityStateError, resolve_public_identity_mode
from public_release_catalog import PublicReleaseCatalogError, validate_catalog

MAX_CONFIG = 32 * 1024
MAX_SESSION = 16 * 1024
MAX_CATALOG = 256 * 1024


class StagingPreflightError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def validate_staging_origin(value: str) -> str:
    """Only explicitly selected HTTPS staging/preview hosts may be probed."""
    if not isinstance(value, str) or value != value.strip():
        raise StagingPreflightError("staging-origin-invalid")
    try:
        parsed = urlsplit(value)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        requested_port = parsed.port
    except ValueError as error:
        raise StagingPreflightError("staging-origin-invalid") from error
    if (parsed.scheme != "https" or not hostname or parsed.username or parsed.password
            or requested_port not in (None, 443) or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or parsed.netloc.endswith(".")):
        raise StagingPreflightError("staging-origin-invalid")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise StagingPreflightError("staging-origin-ip-address-forbidden")
    if hostname in {"localhost", "ordax.com.br", "www.ordax.com.br"} or hostname.endswith(".local"):
        raise StagingPreflightError("staging-origin-production-or-local")
    labels = hostname.split(".")
    if (len(labels) < 2 or not all(label and label.isascii() and
            all(c.isalnum() or c == "-" for c in label) and
            not label.startswith("-") and not label.endswith("-") for label in labels)):
        raise StagingPreflightError("staging-origin-host-invalid")
    # Explicit staging/preview naming prevents accidentally using an arbitrary
    # production host. This is not a certificate of environment ownership.
    if not ({"staging", "preview"} & set(labels)
            or hostname.endswith((".vercel.app", ".pages.dev"))):
        raise StagingPreflightError("staging-origin-not-explicit")
    return "https://" + hostname


def _fetch_json(origin: str, path: str, maximum: int) -> tuple[int, dict]:
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    req = Request(origin + path, headers={
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "User-Agent": "OrdaX-Site-Staging-Preflight/1",
    }, method="GET")
    try:
        response = opener.open(req, timeout=10)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError) as error:
        raise StagingPreflightError("staging-network-unavailable") from error
    with response:
        status = response.status
        if status not in (200, 503):
            raise StagingPreflightError("unexpected-response-status:" + path)
        if response.geturl() != origin + path:
            raise StagingPreflightError("redirect-or-origin-mismatch:" + path)
        media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            raise StagingPreflightError("json-content-type:" + path)
        if path == "/auth/session" and "no-store" not in response.headers.get("Cache-Control", "").lower():
            raise StagingPreflightError("session-not-no-store")
        advertised = response.headers.get("Content-Length")
        if advertised is not None and (not advertised.isdigit() or int(advertised) > maximum):
            raise StagingPreflightError("response-too-large:" + path)
        raw = response.read(maximum + 1)
        if len(raw) > maximum:
            raise StagingPreflightError("response-too-large:" + path)
        try:
            result = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            raise StagingPreflightError("invalid-json:" + path) from error
        if not isinstance(result, dict):
            raise StagingPreflightError("json-object-required:" + path)
        return status, result


def evaluate_gateway_contracts(fetch_json) -> dict:
    """Check existing canonical contracts; accepts an injectable read-only fetch."""
    config_status, config = fetch_json("/config/public-site.json", MAX_CONFIG)
    if config_status != 200 or config.get("$schema") != "prototype-ordax.public-site-runtime/1":
        raise StagingPreflightError("site-runtime-contract-invalid")
    downloads = config.get("downloads")
    product = config.get("product")
    web = product.get("web") if isinstance(product, dict) else None
    if not isinstance(downloads, dict) or downloads.get("catalog_url") != "/releases/catalog.json":
        raise StagingPreflightError("catalog-not-canonical-same-origin")
    if not isinstance(web, dict) or web.get("enabled") is not False:
        raise StagingPreflightError("web-product-not-gated")
    session_status, session = fetch_json("/auth/session", MAX_SESSION)
    try:
        identity_mode = resolve_public_identity_mode(
            config, session, session_http_status=session_status
        )
    except PublicIdentityStateError as error:
        raise StagingPreflightError("identity-contract:" + str(error)) from error
    if identity_mode == "disabled-unconfigured":
        raise StagingPreflightError("identity-gateway-not-configured")
    if identity_mode == "gated":
        raise StagingPreflightError("identity-gateway-still-gated")
    catalog_status, catalog = fetch_json("/releases/catalog.json", MAX_CATALOG)
    if catalog_status != 200:
        raise StagingPreflightError("catalog-http-status-invalid")
    # Reuse the Site's canonical catalog validator, not a second schema.
    with tempfile.TemporaryDirectory(prefix="ordax-site-staging-proof-") as tmp:
        path = Path(tmp) / "catalog.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        try:
            checked = validate_catalog(path)
        except PublicReleaseCatalogError as error:
            raise StagingPreflightError("catalog-contract-invalid") from error
    # Until an owner-published attestation is integrated, a "ready" catalog
    # in staging does not prove trustworthy public download authorization.
    if checked["status"] != "empty" or checked["releases"]:
        raise StagingPreflightError("catalog-unattested-publications")
    return {
        "result": "PASS",
        "scope": "anonymous-staging-contracts-only",
        "identity_mode": identity_mode,
        "catalog_status": checked["status"],
        "authenticated_e2e": "NOT_TESTED",
        "publisher_attestation": "NOT_TESTED",
        "production_approval": False,
    }


def run(staging_origin: str) -> dict:
    origin = validate_staging_origin(staging_origin)
    return evaluate_gateway_contracts(lambda path, maximum: _fetch_json(origin, path, maximum))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-origin", required=True,
                        help="Explicit HTTPS preview/staging origin, never production")
    args = parser.parse_args()
    report = run(args.staging_origin)
    print("SITE_STAGING_PREFLIGHT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except StagingPreflightError as error:
        raise SystemExit("SITE_STAGING_PREFLIGHT=BLOCKED reason=" + str(error))
