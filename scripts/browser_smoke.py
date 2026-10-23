#!/usr/bin/env python3
"""Local, non-deploy browser proof for an already-verified static Site artifact.

Uses Python stdlib + ChromeDriver preinstalled on GitHub's pinned Ubuntu image.
No browser package or OS/Surface checkout is required.
"""
from __future__ import annotations

import argparse
import base64
import http.server
import json
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from site_routes import PATHS as ROUTES
VIEWPORTS = ((1440, 900), (390, 844), (320, 740))


class BrowserProofError(RuntimeError):
    pass


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, root: Path, **kwargs):
        super().__init__(*args, directory=str(root), **kwargs)

    def log_message(self, _format, *_args):
        pass

    def do_POST(self):
        self.send_response(503)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b'{"error":"service-unavailable"}')

    def do_GET(self):
        if self.path.startswith(("/auth/", "/account/", "/api/", "/sync/")):
            self.send_response(503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b'{"error":"service-unavailable"}')
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


def free_port():
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


class Driver:
    def __init__(self, port: int):
        self.base = f"http://127.0.0.1:{port}"
        self.session_id = None

    def command(self, method: str, suffix: str, payload=None):
        req = urllib.request.Request(
            self.base + suffix,
            data=(json.dumps(payload).encode("utf-8") if payload is not None else None),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            content = exc.read().decode("utf-8", "replace")
            raise BrowserProofError(f"{method} {suffix}: {exc.code} {content[:500]}") from exc
        if isinstance(result.get("value"), dict) and result["value"].get("error"):
            raise BrowserProofError(str(result["value"]))
        return result.get("value")

    def create(self):
        response = self.command("POST", "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "chrome",
                "goog:chromeOptions": {"args": [
                    "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                    "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                    "--window-size=1440,900",
                ]},
            }}
        })
        # W3C response returns {sessionId,capabilities} under value.
        self.session_id = response["sessionId"]
        self.command("POST", f"/session/{self.session_id}/timeouts", {
            "pageLoad": 30000, "script": 15000, "implicit": 0
        })

    def run(self, script: str):
        return self.command("POST", f"/session/{self.session_id}/execute/sync", {
            "script": script, "args": []
        })

    def cdp(self, cmd: str, params: dict):
        return self.command("POST", f"/session/{self.session_id}/goog/cdp/execute", {
            "cmd": cmd, "params": params
        })

    def navigate(self, url: str):
        self.command("POST", f"/session/{self.session_id}/url", {"url": url})

    def press(self, value: str):
        # W3C hardware keyboard action, not a DOM .click() substitute.
        self.command("POST", f"/session/{self.session_id}/actions", {
            "actions": [{"type": "key", "id": "keyboard", "actions": [
                {"type": "keyDown", "value": value},
                {"type": "keyUp", "value": value},
            ]}]
        })
        self.command("DELETE", f"/session/{self.session_id}/actions")

    def shot(self, destination: Path):
        content = self.command("GET", f"/session/{self.session_id}/screenshot")
        destination.write_bytes(base64.b64decode(content))

    def close(self):
        if self.session_id:
            try:
                self.command("DELETE", f"/session/{self.session_id}")
            except (BrowserProofError, OSError):
                pass


def probe(driver: Driver, route: str, width: int, height: int) -> dict:
    return driver.run(r"""return (() => {
      const route = location.pathname;
      const $ = s => document.querySelector(s);
      const body = document.body;
      const main = $('main');
      const forms = [...document.querySelectorAll('form.identity-form')];
      const visibleAuthForms = forms.filter(x => !x.hidden);
      const readyControls = forms.flatMap(f => [...f.querySelectorAll('input[type=password],button[type=submit]')]).filter(x => !x.disabled);
      const els = [...document.querySelectorAll('[id]')];
      const ids = els.map(e => e.id);
      const controls = [...document.querySelectorAll('a[href],button,input,select,textarea')].filter(e => {
        const box = e.getBoundingClientRect();
        return box.width > 0 && box.height > 0 && getComputedStyle(e).visibility !== 'hidden';
      });
      const nameless = controls.filter(e => {
        if (e.getAttribute('aria-hidden') === 'true' || e.disabled) return false;
        if (e.matches('input[type=hidden]')) return false;
        const name = e.getAttribute('aria-label') || e.getAttribute('title') ||
          (e.id && document.querySelector('label[for="' + CSS.escape(e.id) + '"]')?.textContent) ||
          e.closest('label')?.textContent || e.textContent || e.getAttribute('alt');
        return !String(name || '').trim() && !e.querySelector('img[alt]');
      }).slice(0, 6).map(e => e.outerHTML.slice(0, 200));
      const unlabeledImages = [...document.querySelectorAll('img:not([alt])')].filter(x =>
        x.getBoundingClientRect().width > 0).map(x => x.outerHTML.slice(0, 200)).slice(0, 8);
      const unexpectedRemote = performance.getEntriesByType('resource')
        .map(x => x.name).filter(x => !x.startsWith(location.origin) && !x.startsWith('data:'));
      const session = $('[data-identity-state],#account-session,[data-web-state]');
      return {
        pathname: route,
        width: innerWidth,
        height: innerHeight,
        title: document.title,
        lang: document.documentElement.lang,
        complete: document.readyState === 'complete',
        main: !!main,
        mainCount: document.querySelectorAll('main').length,
        skip: !!$('.skip-link[href^="#"]'),
        noOverflow: document.documentElement.scrollWidth <= innerWidth + 2,
        scrollWidth: document.documentElement.scrollWidth,
        duplicateIds: ids.length !== new Set(ids).size,
        nameless,
        unlabeledImages,
        remoteResources: unexpectedRemote,
        authFormCount: forms.length,
        exposedAuthForms: visibleAuthForms.length,
        enabledCredentials: readyControls.length,
        sessionStatus: session?.dataset?.status || null,
        accountHasVerifiedUser: !!document.querySelector('[data-verified-user]') ||
          [...document.querySelectorAll('.verified-email')].some(x => x.textContent.includes('@')),
        landingFixturePresent: !!document.querySelector('.playground[data-fixture-ready="true"]') &&
          !!document.querySelector('.playground .demo-native'),
        accountPortal: !!document.querySelector('#account-app'),
        interactiveCount: controls.length
      };
    })();""")


def accessibility_probe(driver: Driver) -> dict:
    """Read the browser accessibility tree and exercise real keyboard navigation."""
    ax = driver.cdp("Accessibility.getFullAXTree", {})
    interactive = {"button", "link", "textbox", "searchbox", "combobox",
                   "checkbox", "radio", "switch"}
    missing_names = []
    for node in ax.get("nodes", []):
        role = node.get("role", {}).get("value", "")
        if (not node.get("ignored", False) and role in interactive
                and not str(node.get("name", {}).get("value", "")).strip()):
            missing_names.append({
                "role": role,
                "backendDOMNodeId": node.get("backendDOMNodeId"),
            })
    # Once per page, exercise the first focusable keyboard target and the
    # actual Enter activation instead of assuming that the skip link works.
    driver.press("\ue004")
    # The actual focus-reveal animation has a 180ms CSS transition.
    time.sleep(0.25)
    first = driver.run("""return (() => {
      const focused = document.activeElement;
      const rect = focused?.getBoundingClientRect();
      const styles = focused && getComputedStyle(focused);
      return {
        skipFocused: focused?.matches?.('.skip-link[href="#conteudo"]') || false,
        focusVisible: Boolean(rect && rect.width > 0 && rect.height > 0
          && rect.bottom > 0 && rect.top < innerHeight
          && styles.visibility !== 'hidden'),
      };
    })();""")
    driver.press("\ue007")
    time.sleep(0.1)
    destination = driver.run("""return {
      hash: location.hash,
      mainFocus: document.activeElement?.id === 'conteudo',
      mainExists: !!document.querySelector('#conteudo'),
    };""")
    return {
        "accessibilityTreeUnnamedControls": missing_names[:12],
        "skipLinkFirstKeyboardTarget": first["skipFocused"],
        "skipLinkVisibleOnFocus": first["focusVisible"],
        "skipLinkDestination": destination["mainExists"] and
          (destination["hash"] == "#conteudo" or destination["mainFocus"]),
        "skipLinkFocusLandsOnMain": destination["mainFocus"],
    }


def run(root: Path, evidence: Path) -> dict:
    if not (root / "public-site-manifest.json").is_file():
        raise BrowserProofError("build candidate missing; never browse unpackaged source")
    if not shutil.which("chromedriver") or not shutil.which("google-chrome"):
        raise BrowserProofError("Chrome + ChromeDriver required on pinned CI runner")
    evidence.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *a, **k: Handler(*a, root=root, **k),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    webdriver_port = free_port()
    command = ["chromedriver", f"--port={webdriver_port}", "--allowed-ips=127.0.0.1"]
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    driver = Driver(webdriver_port)
    results = []
    failures = []
    try:
        for _ in range(100):
            if child.poll() is not None:
                raise BrowserProofError("ChromeDriver stopped before accepting a session")
            try:
                with urllib.request.urlopen(driver.base + "/status", timeout=1):
                    break
            except (urllib.error.URLError, OSError):
                time.sleep(0.1)
        else:
            raise BrowserProofError("ChromeDriver did not start")
        driver.create()
        for route in ROUTES:
            for width, height in VIEWPORTS:
                driver.cdp("Emulation.setDeviceMetricsOverride", {
                    "width": width, "height": height, "deviceScaleFactor": 1,
                    "mobile": width <= 430,
                })
                url = f"http://127.0.0.1:{server.server_port}{route}"
                driver.navigate(url)
                # Auth/readiness can be asynchronous. No user data or privileged
                # service is available: all API requests fail closed at loopback.
                for _ in range(35):
                    if driver.run("return document.readyState === 'complete'"):
                        break
                    time.sleep(0.1)
                if route == "/":
                    for _ in range(40):
                        done = driver.run("""return document.querySelector('.playground')?.dataset.fixtureReady || null;""")
                        if done in ("true", "false"):
                            break
                        time.sleep(0.1)
                if route in ("/login/", "/cadastro/", "/recuperar/", "/recuperar/nova-senha/", "/conta/", "/web/"):
                    for _ in range(30):
                        status = driver.run("""const el=document.querySelector('[data-identity-state],#account-session,[data-web-state]'); return el?.dataset?.status || null;""")
                        if status not in (None, "checking"):
                            break
                        time.sleep(0.1)
                report = probe(driver, route, width, height)
                # The viewport and browser accessibility tree are audited on
                # every route. Keyboard travel is tested on desktop only:
                # the same page markup and tab order is shared with mobile.
                if width == VIEWPORTS[0][0]:
                    report.update(accessibility_probe(driver))
                short = route.strip("/").replace("/", "-") or "home"
                filename = f"{short}-{width}x{height}.png"
                driver.shot(evidence / filename)
                report.update({"expectedRoute": route, "screenshot": filename})
                results.append(report)
                check = {
                    "loaded": report["complete"] and report["pathname"] == route and report["mainCount"] == 1,
                    "correctLanguage": report["lang"] in ("pt-BR", "en-US"),
                    "namedDocument": bool(report["title"]),
                    "skipNavigation": report["skip"],
                    "noHorizontalOverflow": report["noOverflow"],
                    "uniqueElementIds": not report["duplicateIds"],
                    "accessibleInteractiveNames": not report["nameless"],
                    "visibleImagesHaveAltAttribute": not report["unlabeledImages"],
                    "noUnexpectedRemoteRequests": not report["remoteResources"],
                }
                if width == VIEWPORTS[0][0]:
                    check.update({
                        "accessibilityTreeNames": not report["accessibilityTreeUnnamedControls"],
                        "skipLinkKeyboardFirst": report["skipLinkFirstKeyboardTarget"],
                        "skipLinkKeyboardVisible": report["skipLinkVisibleOnFocus"],
                        "skipLinkKeyboardNavigates": report["skipLinkDestination"],
                        "skipLinkKeyboardFocus": report["skipLinkFocusLandsOnMain"],
                    })
                if route in ("/login/", "/cadastro/", "/recuperar/", "/recuperar/nova-senha/"):
                    check.update({"formsFailClosed": not report["exposedAuthForms"] and not report["enabledCredentials"]})
                if route == "/conta/":
                    check.update({"accountShellPresent": report["accountPortal"],
                                  "noInventedVerifiedUser": not report["accountHasVerifiedUser"]})
                if route == "/":
                    check["landingFixturePresent"] = report["landingFixturePresent"]
                for name, success in check.items():
                    if not success:
                        failures.append({"route": route, "viewport": width, "rule": name,
                                         "summary": report})
        output = {"schema": "ordax.site-browser-proof/1", "routeCount": len(ROUTES),
                  "viewportCount": len(VIEWPORTS), "checks": len(results),
                  "failures": failures, "results": results}
        (evidence / "report.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if failures:
            raise BrowserProofError(f"{len(failures)} browser checks failed; see report.json; "
                                    + "; ".join(f"{r['route']}@{r['viewport']}:{r['rule']}" for r in failures[:15]))
        return output
    finally:
        driver.close()
        child.terminate()
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="out/site")
    parser.add_argument("--evidence", default="out/browser-evidence")
    args = parser.parse_args()
    output = run(Path(args.out).resolve(), Path(args.evidence).resolve())
    print(f"SITE_BROWSER_PROOF=PASS routes={output['routeCount']} viewports={output['viewportCount']} checks={output['checks']}")


if __name__ == "__main__":
    try:
        main()
    except (BrowserProofError, OSError, ValueError) as error:
        raise SystemExit(f"SITE_BROWSER_PROOF=FAIL {error}")
