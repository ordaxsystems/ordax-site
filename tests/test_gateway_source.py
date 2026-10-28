"""Offline tests for the immutable, non-production OS gateway source consumer."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_canonical_gateway as gateway


class GatewaySourceTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(gateway.LOCK.read_text(encoding="utf-8"))

    def fixture(self):
        values = {row["path"]: b"export const fixture = true;\n" for row in self.lock["files"]}
        values[gateway.ENTRY] = b'export { default } from "../lib/account-proxy-core.mjs";\n'
        fixture = copy.deepcopy(self.lock)
        for row in fixture["files"]:
            payload = values[row["path"]]
            row["size"] = len(payload)
            row["git_blob_sha1"] = gateway.git_blob_sha1(payload)
        return fixture, values

    def test_exact_lock_is_valid_and_source_is_staging_only(self):
        self.assertEqual(gateway.validate_lock(self.lock), self.lock)
        self.assertEqual(self.lock["status"], gateway.STATUS)
        self.assertEqual(self.lock["repository"], gateway.REPOSITORY)
        self.assertTrue(all(entry["path"].endswith(".mjs") for entry in self.lock["files"]))

    def test_atomically_materializes_only_verified_files(self):
        lock, values = self.fixture()
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "source"
            def fetch(commit, path, size):
                self.assertEqual(commit, lock["commit"])
                self.assertEqual(size, len(values[path]))
                return values[path]
            result = gateway.materialize(lock, output, fetch)
            self.assertEqual(result["status"], "verified-staging-only")
            self.assertEqual(result["verified_files"], len(values))
            self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob("*.mjs")}, set(values))
            with self.assertRaisesRegex(gateway.GatewaySourceError, "must-not-exist"):
                gateway.materialize(lock, output, fetch)

    def test_modified_or_truncated_source_fails_closed_without_any_output(self):
        lock, values = self.fixture()
        for change in (lambda v: v + b" ", lambda v: v[:-1]):
            with tempfile.TemporaryDirectory() as root:
                output = Path(root) / "source"
                def tampered(commit, path, size):
                    original = values[path]
                    return change(original) if path == gateway.ENTRY else original
                with self.assertRaisesRegex(gateway.GatewaySourceError, "mismatch"):
                    gateway.materialize(lock, output, tampered)
                self.assertFalse(output.exists())

    def test_outside_import_fails_closed_even_for_a_valid_git_blob(self):
        lock, values = self.fixture()
        path = gateway.ENTRY
        values[path] = b'export * from "../lib/unknown.mjs";\n'
        target = next(row for row in lock["files"] if row["path"] == path)
        target["git_blob_sha1"] = gateway.git_blob_sha1(values[path])
        target["size"] = len(values[path])
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "source"
            with self.assertRaisesRegex(gateway.GatewaySourceError, "outside-locked-closure"):
                gateway.materialize(lock, output, lambda _c, p, _s: values[p])
            self.assertFalse(output.exists())

    def test_authority_path_and_size_guards(self):
        for change in (
            lambda v: v.update({"status": "production"}),
            lambda v: v.update({"repository": "attacker/ordax-os"}),
            lambda v: v.update({"commit": "main"}),
            lambda v: v["files"][0].update({"path": "api/../../oops.mjs"}),
            lambda v: v["files"][0].update({"size": True}),
            lambda v: v["files"].append(copy.deepcopy(v["files"][0])),
            lambda v: v["files"].pop(0),
            lambda v: v["files"][0].update({"git_blob_sha1": "0"}),
        ):
            altered = copy.deepcopy(self.lock)
            change(altered)
            with self.subTest(change=str(change)), self.assertRaises(gateway.GatewaySourceError):
                gateway.validate_lock(altered)


if __name__ == "__main__":
    unittest.main()
