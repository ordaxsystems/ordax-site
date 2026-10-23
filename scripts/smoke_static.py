#!/usr/bin/env python3
"""Static candidate checks for all routes; no remote browser, auth or deploy access."""
from __future__ import annotations
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROUTES = (
    "index.html", "download/index.html", "login/index.html",
    "cadastro/index.html", "recuperar/index.html",
    "recuperar/nova-senha/index.html", "conta/index.html",
    "licencas/index.html", "privacidade/index.html", "termos/index.html",
    "web/index.html",
)

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.in_title = False
        self.title = ""
        self.headings = 0
        self.mains = 0
        self.description = ""
        self.viewport = ""
        self.robots = ""
        self.ids = set()
        self.skip_target = None
        self.assets = []
        self.forms = []
        self.password_inputs = []
        self.submit_buttons = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "html": self.lang = attr.get("lang", "")
        if tag == "title": self.in_title = True
        if tag == "main": self.mains += 1
        if tag == "h1": self.headings += 1
        if "id" in attr: self.ids.add(attr["id"])
        if tag == "meta":
            if attr.get("name") == "description": self.description = attr.get("content", "")
            if attr.get("name") == "viewport": self.viewport = attr.get("content", "")
            if attr.get("name") == "robots": self.robots = attr.get("content", "")
        if tag == "link" and attr.get("rel") in {"stylesheet", "icon"}:
            self.assets.append(attr.get("href", ""))
        if tag in {"script", "img"} and attr.get("src"):
            self.assets.append(attr["src"])
        if tag == "a" and attr.get("class") == "skip-link":
            self.skip_target = attr.get("href")
        if tag == "form": self.forms.append(attr)
        if tag == "input" and attr.get("type") == "password":
            self.password_inputs.append(attr)
        if tag == "button" and attr.get("type") == "submit":
            self.submit_buttons.append(attr)

    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.title += data

def assert_candidate(out: Path) -> dict:
    if not (out / "public-site-manifest.json").is_file():
        raise AssertionError("candidate manifest is absent")
    inspected = []
    for relative in ROUTES:
        html = (out / relative).read_text(encoding="utf-8")
        page = Page()
        page.feed(html)
        checks = {
            "html language": page.lang == "pt-BR",
            "document title": bool(page.title.strip()),
            "meta description": bool(page.description.strip()),
            "viewport": "width=device-width" in page.viewport,
            "single main": page.mains == 1,
            "primary heading": page.headings >= 1 or (relative == "conta/index.html" and 'id="account-content"' in html),
            "skip navigation": page.skip_target in {"#" + identifier for identifier in page.ids},
        }
        for key, good in checks.items():
            if not good:
                raise AssertionError(relative + ": " + key + " failed")
        for value in page.assets:
            url = urlsplit(value)
            if url.scheme or url.netloc or not value.startswith("/"):
                raise AssertionError(relative + ": remote/relative active asset " + value)
            if ".." in url.path.split("/"):
                raise AssertionError(relative + ": unsafe resource path " + value)
            if not (out / url.path.lstrip("/")).is_file():
                raise AssertionError(relative + ": missing referenced asset " + value)
        if relative in {"login/index.html", "cadastro/index.html", "recuperar/index.html", "recuperar/nova-senha/index.html"}:
            if not page.forms:
                raise AssertionError(relative + ": guarded native form missing")
            if any("hidden" not in form or form.get("action") for form in page.forms):
                raise AssertionError(relative + ": credential form published as active")
            if any("disabled" not in field for field in page.password_inputs):
                raise AssertionError(relative + ": password input active without server readiness")
            if any("disabled" not in button for button in page.submit_buttons):
                raise AssertionError(relative + ": credential submission active without server readiness")
        if relative == "index.html":
            if 'id="playground-fixture"' in html:
                raise AssertionError("landing embeds a duplicate fixture instead of the canonical JSON asset")
            fixture = out / "assets/playground-fixture.json"
            if not fixture.is_file() or not json.loads(fixture.read_text("utf-8")).get("surface"):
                raise AssertionError("standalone playground fixture is missing or malformed")
            if 'fetch("/assets/playground-fixture.json"' not in (out / "assets/playground.js").read_text("utf-8"):
                raise AssertionError("playground controller must consume only the canonical fixture")
        if relative == "conta/index.html" and "noindex" not in page.robots:
            raise AssertionError(relative + ": account portal must not be indexed")
        if relative in {"index.html", "conta/index.html"}:
            if html.count('class="commercial-plan"') != 4:
                raise AssertionError(relative + ": reference offers parity with canonical catalog failed")
            if "Planos em preparação" not in html or "contratação indisponível" not in html:
                raise AssertionError(relative + ": inactive commercial availability not explicit")
            if "ORDAX_PUBLIC_PLAN_CATALOG" in html or "ORDAX_ACCOUNT_PLAN_CATALOG" in html:
                raise AssertionError(relative + ": unresolved reference catalog marker")
        inspected.append({"route": "/" + relative.removesuffix("index.html"), "assets": len(page.assets), "headings": page.headings})
    catalog = json.loads((out / "releases/catalog.json").read_text("utf-8"))
    if catalog != {"$schema": "prototype-ordax.public-release-catalog/1", "status": "empty", "releases": []}:
        raise AssertionError("CI candidate must fail closed on absent authorized publications")
    return {"result": "PASS", "routes": inspected, "default_public_releases": 0}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="out/site")
    args = parser.parse_args()
    print(json.dumps(assert_candidate(Path(args.out)), sort_keys=True, ensure_ascii=False))
