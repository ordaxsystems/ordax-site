#!/usr/bin/env python3
"""Materialize a pinned OS-owned gateway source closure for isolated staging.

This does not create a runnable Site backend or authorize any identity
environment. Generated files are disposable; source authority remains ordax-os.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "contracts/canonical-gateway-source.json"
SCHEMA = "ordax.site-canonical-gateway-source/1"
STATUS = "staging-only-not-authorized-for-production"
REPOSITORY = "ordaxsystems/ordax-os"
ENTRY = "api/account-proxy.mjs"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SOURCE_PATH = re.compile(r"(?:api/|lib/|infra/supabase/functions/)[a-zA-Z0-9_./-]+\.mjs\Z")
STATIC_IMPORT = re.compile(r"""(?:\bfrom\s*|\bimport\s*)[\x22\x27](\.[^\x22\x27]+)[\x22\x27]""")
MAX_FILES = 16
MAX_BYTES = 128 * 1024


class GatewaySourceError(ValueError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def validate_lock(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"$schema", "status", "repository", "commit", "files"}:
        raise GatewaySourceError("gateway-lock-schema-invalid")
    if (value["$schema"] != SCHEMA or value["status"] != STATUS
            or value["repository"] != REPOSITORY
            or not isinstance(value["commit"], str)
            or not SHA40.fullmatch(value["commit"])):
        raise GatewaySourceError("gateway-lock-authority-invalid")
    rows = value["files"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= MAX_FILES:
        raise GatewaySourceError("gateway-lock-files-invalid")
    seen = set()
    total = 0
    for entry in rows:
        if not isinstance(entry, dict) or set(entry) != {"path", "git_blob_sha1", "size"}:
            raise GatewaySourceError("gateway-lock-entry-invalid")
        path, sha, size = entry["path"], entry["git_blob_sha1"], entry["size"]
        if (not isinstance(path, str) or not SOURCE_PATH.fullmatch(path)
                or any(part in (".", "..", "") for part in path.split("/"))
                or path in seen or not isinstance(sha, str) or not SHA40.fullmatch(sha)
                or not isinstance(size, int) or isinstance(size, bool) or size < 1):
            raise GatewaySourceError("gateway-lock-entry-invalid")
        seen.add(path)
        total += size
    if ENTRY not in seen or "lib/account-proxy-core.mjs" not in seen or total > MAX_BYTES:
        raise GatewaySourceError("gateway-lock-incomplete")
    return value


def verify_closure(sources: dict[str, bytes]) -> None:
    expected = set(sources)
    for path, raw in sources.items():
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GatewaySourceError("gateway-module-not-utf8:" + path) from error
        # All static relative imports must resolve within the immutable lock.
        for relative in STATIC_IMPORT.findall(text):
            destination = posixpath.normpath(posixpath.join(posixpath.dirname(path), relative))
            if destination not in expected:
                raise GatewaySourceError("gateway-import-outside-locked-closure:" + path)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def fetch_owner_source(commit: str, path: str, size: int) -> bytes:
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/{quote(path, safe='/')}"
    opener = build_opener(NoRedirect())
    request = Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "OrdaX-Site-Gateway-Source/1"})
    try:
        response = opener.open(request, timeout=15)
        with response:
            if response.status != 200 or response.geturl() != url:
                raise GatewaySourceError("gateway-owner-origin-invalid")
            payload = response.read(size + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise GatewaySourceError("gateway-owner-unavailable") from error
    if len(payload) != size:
        raise GatewaySourceError("gateway-source-size-mismatch:" + path)
    return payload


def materialize(lock: dict[str, object], output: Path, fetcher=fetch_owner_source) -> dict[str, object]:
    """Fetch, verify and stage all files as a transaction. No partial output."""
    validate_lock(lock)
    sources = {}
    for entry in lock["files"]:
        path = entry["path"]
        raw = fetcher(lock["commit"], path, entry["size"])
        if not isinstance(raw, bytes) or len(raw) != entry["size"]:
            raise GatewaySourceError("gateway-source-size-mismatch:" + path)
        if git_blob_sha1(raw) != entry["git_blob_sha1"]:
            raise GatewaySourceError("gateway-source-blob-mismatch:" + path)
        sources[path] = raw
    verify_closure(sources)
    if output.exists():
        raise GatewaySourceError("gateway-output-must-not-exist")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".gateway-source-", dir=output.parent) as temp:
        staged = Path(temp) / "source"
        for path, data in sources.items():
            destination = staged / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        staged.rename(output)
    return {"status": "verified-staging-only", "repository": REPOSITORY,
            "source_commit": lock["commit"], "verified_files": len(sources)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=LOCK)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    report = materialize(lock, args.out.resolve())
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
