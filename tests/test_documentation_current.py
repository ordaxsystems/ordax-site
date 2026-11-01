"""Keep active Dev instructions consistent with executable owner contracts.

History is intentionally preserved under docs/history and must never be treated
as an operational runbook.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = (
    "README.md",
    "AGENTS.md",
    "docs/HANDOFF.md",
    "docs/AUDIT.md",
    "docs/ACCESSIBILITY-GATES.md",
)


class CurrentDocsTests(unittest.TestCase):
    def test_active_docs_do_not_reference_removed_migration_artifacts_as_inputs(self):
        removed = (
            "contracts/migration-artifact-lock.json",
            "artifacts/brand/os-migration-70b0f7eb",
            "artifacts/offers/os-migration-70b0f7eb",
            "artifacts/surface-preview/os-migration-70b0f7eb",
        )
        for relative in ACTIVE:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for legacy in removed:
                with self.subTest(file=relative, legacy=legacy):
                    self.assertNotIn(legacy, text)
        self.assertNotIn("--migration-lock", (ROOT / "README.md").read_text())
        self.assertNotIn("--migration-lock", (ROOT / "AGENTS.md").read_text())

    def test_build_instructions_match_current_single_dev_lock(self):
        lock_path = "contracts/dev-artifact-lock.json"
        doc = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        a11y = (ROOT / "docs/ACCESSIBILITY-GATES.md").read_text(encoding="utf-8")
        for contents in (doc, agents, a11y):
            self.assertIn(lock_path, contents)
            self.assertIn("--dev-lock", contents)
        lock = json.loads((ROOT / lock_path).read_text(encoding="utf-8"))
        self.assertEqual(lock["$schema"], "ordax.site-dev-artifact-lock/2")
        self.assertEqual(set(lock["artifacts"]), {"brand", "surface_preview"})
        self.assertEqual(
            {record["release"]["source_repository"] for record in lock["artifacts"].values()},
            {"ordaxsystems/ordax-surface"},
        )

    def test_active_host_guidance_matches_existing_gateway_owner_contracts(self):
        # Documentation is not a second deployment SSOT: it must describe the
        # executable Vercel adapter and the one immutable OS-owned source lock.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs/HANDOFF.md").read_text(encoding="utf-8")
        vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "contracts/canonical-gateway-source.json").read_text(encoding="utf-8"))
        for value in (readme, agents, handoff):
            self.assertIn("api/account-proxy.mjs", value)
            self.assertIn("contracts/canonical-gateway-source.json", value)
            self.assertIn("ordax-site", value)
        self.assertNotIn("sem Identity/gateway", readme)
        self.assertNotIn("O preview `ordax-site` próprio permanece uma dependência", agents)
        self.assertEqual(lock["repository"], "ordaxsystems/ordax-os")
        self.assertEqual(lock["status"], "staging-only-not-authorized-for-production")
        self.assertIn("stage_canonical_gateway.py --out .gateway-source", vercel["installCommand"])
        self.assertEqual(
            [row["source"] for row in vercel["rewrites"]],
            ["/auth/:path*", "/sync/:path*", "/account/:path*"],
        )
        self.assertNotIn("domains", vercel)
        self.assertIn("X-Robots-Tag", str(vercel["headers"]))
        self.assertIn("noindex", str(vercel["headers"]))

    def test_adr_ids_are_unique_and_old_runbooks_are_explicitly_archived(self):
        decisions = (ROOT / "docs/DECISIONS.md").read_text(encoding="utf-8")
        ids = re.findall(r"\*\*SITE-ADR-(\d{3})", decisions)
        self.assertGreaterEqual(len(ids), 33)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("**SITE-ADR-033", decisions)
        self.assertIn("**SITE-ADR-032", decisions)
        for name in ("SITE-CUTOVER-2026-10-24.md", "SITE-AUDIT-2026-10-24.md"):
            text = (ROOT / "docs/history" / name).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("> **Arquivo histórico imutável"))
        self.assertIn("history/SITE-CUTOVER-2026-10-24.md",
                      (ROOT / "docs/HANDOFF.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
