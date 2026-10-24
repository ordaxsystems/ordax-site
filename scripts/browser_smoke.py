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
NO_SCRIPT_ROUTES = ("/login/", "/cadastro/", "/recuperar/",
                    "/recuperar/nova-senha/", "/conta/", "/web/")
# 1280px layout viewed through 200% and 400% effective CSS viewports.
# This checks responsive reflow, not real browser zoom or text magnification.
REFLOW_WIDTHS = ((640, 200), (320, 400))


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
        # Install before any Site script runs. A syntactically broken module
        # must not pass merely because its static HTML still looks correct.
        self.cdp("Page.addScriptToEvaluateOnNewDocument", {"source": r"""
          window.__ordaxPageErrors = [];
          addEventListener('error', event => {
            if (event.target && event.target !== window) {
              const resource = event.target.src || event.target.href || event.target.tagName;
              window.__ordaxPageErrors.push('resource: ' + String(resource).slice(0, 180));
            } else {
              window.__ordaxPageErrors.push('script: ' +
                String(event.message || 'unknown').slice(0, 180));
            }
          }, true);
          addEventListener('unhandledrejection', event => {
            window.__ordaxPageErrors.push('promise: ' +
              String(event.reason?.message || event.reason || 'unknown').slice(0, 180));
          });
        """})

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
      const resources = performance.getEntriesByType('resource');
      const unexpectedRemote = resources
        .map(x => x.name).filter(x => !x.startsWith(location.origin) && !x.startsWith('data:'));
      const failedStaticAssets = resources.filter(x => {
        if (x.responseStatus < 400) return false;
        const path = new URL(x.name, location.href).pathname;
        // Identity endpoints deliberately respond 503 in this offline proof.
        return !['/auth/', '/account/', '/api/', '/sync/'].some(prefix =>
          path.startsWith(prefix));
      }).map(x => ({url: x.name.slice(0, 180), status: x.responseStatus})).slice(0, 8);
      const overflowElements = [...document.querySelectorAll('body *')].filter(el => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return rect.width > 0 && rect.right > innerWidth + 2 &&
          rect.left < innerWidth && style.display !== 'none' &&
          style.visibility !== 'hidden' && style.position !== 'fixed';
      }).slice(0, 18).map(el => {
        const r = el.getBoundingClientRect();
        return {tag:el.tagName.toLowerCase(), className:String(el.className?.baseVal || el.className || '').slice(0, 100),
          width:Math.round(r.width), left:Math.round(r.left), right:Math.round(r.right)};
      });
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
        overflowElements,
        duplicateIds: ids.length !== new Set(ids).size,
        nameless,
        unlabeledImages,
        remoteResources: unexpectedRemote,
        failedStaticAssets,
        runtimeErrors: (window.__ordaxPageErrors || ['browser-error-monitor-missing']).slice(0, 10),
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


def localization_probe(driver: Driver) -> dict:
    """Exercise the actual language selector, including DOM and locale persistence."""
    return driver.run(r"""return (() => {
      const selector = document.querySelector('[data-public-locale-select]');
      const runtime = window.OrdaXPublicI18n;
      if (!selector || !runtime) return {
        selector: false, english: false, portuguese: false, persistence: false
      };
      const apply = value => {
        selector.value = value;
        selector.dispatchEvent(new Event('change', {bubbles:true}));
        return {
          language: document.documentElement.lang,
          stored: localStorage.getItem('ordax.public.locale'),
          selector: selector.value,
          skip: document.querySelector('.skip-link')?.textContent?.trim(),
        };
      };
      const english = apply('en-US');
      const portuguese = apply('pt-BR');
      return {
        selector: true,
        english: english.language === 'en-US' &&
          english.stored === 'en-US' &&
          english.selector === 'en-US' &&
          english.skip === 'Skip to content',
        portuguese: portuguese.language === 'pt-BR' &&
          portuguese.stored === 'pt-BR' &&
          portuguese.selector === 'pt-BR' &&
          portuguese.skip === 'Ir para o conteúdo',
        persistence: localStorage.getItem('ordax.public.locale') === 'pt-BR'
      };
    })();""")


def solid_surface_contrast_probe(driver: Driver) -> dict:
    """Measure WCAG 2.x text contrast only when the visible backing is a flat color.

    Gradients, images, alpha effects, decorative demo, and pseudo elements are
    out of scope; never treat an unverifiable surface as a passing measurement.
    """
    return driver.run(r"""return (() => {
      const parse = raw => {
        const m = String(raw).match(/^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s\/]+([\d.]+))?\s*\)$/i);
        return m ? [+m[1], +m[2], +m[3], m[4] == null ? 1 : +m[4]] : null;
      };
      const blend = (front, back) => {
        const a = front[3];
        return [front[0]*a + back[0]*(1-a),
                front[1]*a + back[1]*(1-a),
                front[2]*a + back[2]*(1-a), 1];
      };
      const luminance = rgb => {
        const linear = rgb.slice(0,3).map(v => {
          const c=v/255; return c <= 0.04045 ? c/12.92 : ((c+0.055)/1.055)**2.4;
        });
        return 0.2126*linear[0] + 0.7152*linear[1] + 0.0722*linear[2];
      };
      const ratio = (a,b) => {
        const [high,low]=[luminance(a),luminance(b)].sort((x,y)=>y-x);
        return (high+0.05)/(low+0.05);
      };
      const selectors = [
        '.site-header a', '.site-header button',
        '.site-header select', '.page-shell h1', '.page-shell h2',
        '.page-shell p', '.page-shell a', '.download-container h2',
        '.download-container p', '.download-container a',
        '.account-ui h1', '.account-ui h2', '.account-ui a',
        '.account-ui p', '.account-ui label',
        '.topbar-center a', '.breadcrumb a', '.page-footer a'
      ];
      const nodes = [...new Set(selectors.flatMap(s => [...document.querySelectorAll(s)]))];
      const failed = [], unchecked = {};
      let measured = 0;
      const skip = why => {unchecked[why] = (unchecked[why] || 0) + 1};
      for (const el of nodes) {
        if (!Array.from(el.childNodes).some(n => n.nodeType===Node.TEXT_NODE && n.textContent.trim())) continue;
        const style=getComputedStyle(el);
        const rect=el.getBoundingClientRect();
        if (el.closest('[hidden], [aria-hidden="true"], .demo-native, .playground') ||
            rect.width<1 || rect.height<1 || style.visibility!=='visible' ||
            style.display==='none' || Number(style.opacity)<1) continue;
        const chain=[];
        for(let p=el; p; p=p.parentElement) chain.unshift(p);
        let background=[255,255,255,1], unmeasurable=false;
        for (const n of chain) {
          const css=getComputedStyle(n);
          if (css.backgroundImage!=='none') {skip('image-or-gradient');unmeasurable=true;break}
          if (Number(css.opacity)<1 || css.mixBlendMode!=='normal' || css.filter!=='none') {
            skip('layer-compositing');unmeasurable=true;break;
          }
          const bg=parse(css.backgroundColor);
          if (!bg){skip('unknown-background');unmeasurable=true;break}
          background=blend(bg,background);
        }
        if (unmeasurable) continue;
        const text=parse(style.color);
        if (!text) {skip('unknown-foreground');continue}
        const foreground=blend(text,background);
        const px=parseFloat(style.fontSize)||0;
        const weight=parseInt(style.fontWeight,10)||400;
        const threshold=(px>=24 || (px>=18.66 && weight>=700)) ? 3 : 4.5;
        const value=ratio(foreground,background);
        measured++;
        if (value+0.0001<threshold) failed.push({
          tag:el.tagName.toLowerCase(),
          selector:el.className && typeof el.className==='string' ? el.className.slice(0,70) : '',
          text:el.textContent.trim().slice(0,65),
          foreground:style.color,
          backing:background.slice(0,3).map(Math.round),
          ratio:+value.toFixed(2),
          minimum:threshold,
        });
      }
      return {measured, failed:failed.slice(0,16), failedCount:failed.length,
              unchecked, scope:'flat-color foreground/background with no image or compositing'};
    })();""")


def no_script_probe(driver: Driver) -> dict:
    """Inspect the offline presentation after loading with script execution blocked."""
    return driver.run(r"""return (() => {
      const forms = [...document.querySelectorAll('form.identity-form')];
      const enabledCredentials = forms.flatMap(form =>
        [...form.querySelectorAll('input,button,select,textarea')])
        .filter(control => !control.disabled).length;
      const exposedForms = forms.filter(form => {
        const style = getComputedStyle(form);
        return !form.hidden && style.display !== 'none' &&
          style.visibility !== 'hidden';
      }).length;
      const notice = [...document.querySelectorAll('noscript')].some(el =>
        el.getClientRects().length > 0 ||
        [...el.querySelectorAll('*')].some(child => child.getClientRects().length > 0));
      return {
        pathname: location.pathname,
        lang: document.documentElement.lang,
        hasMain: document.querySelectorAll('main').length === 1,
        noscriptGuidanceVisible: notice,
        navigationAvailable: !!document.querySelector('a[href="/"]'),
        authFormsExposed: exposedForms,
        enabledAuthControls: enabledCredentials,
        noRuntimeActivated: typeof window.OrdaXPublicI18n === 'undefined',
        accountNotVerified: !document.querySelector('[data-verified-user]') &&
          ![...document.querySelectorAll('.verified-email')].some(x =>
            x.textContent.includes('@')),
        webLaunchUnavailable: !document.querySelector('[data-web-launch]') ||
          document.querySelector('[data-web-launch]').hidden
      };
    })();""")


def wait_for_route(driver: Driver, route: str) -> None:
    """Wait for visible state without depending on a privileged backend."""
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
    if route in NO_SCRIPT_ROUTES:
        for _ in range(30):
            status = driver.run("""const el=document.querySelector('[data-identity-state],#account-session,[data-web-state]'); return el?.dataset?.status || null;""")
            if status not in (None, "checking"):
                break
            time.sleep(0.1)


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
    reflow_results = []
    no_script_results = []
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
                # No user data or privileged service is available; all
                # backend requests remain fail-closed on loopback.
                wait_for_route(driver, route)
                report = probe(driver, route, width, height)
                # The viewport and browser accessibility tree are audited on
                # every route. Keyboard travel is tested on desktop only:
                # the same page markup and tab order is shared with mobile.
                if width == VIEWPORTS[0][0]:
                    report.update(accessibility_probe(driver))
                    report["localeSwitch"] = localization_probe(driver)
                    report["solidSurfaceContrast"] = solid_surface_contrast_probe(driver)
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
                    "noBrokenStaticNetworkAssets": not report["failedStaticAssets"],
                    "noUncaughtBrowserErrors": not report["runtimeErrors"],
                }
                if width == VIEWPORTS[0][0]:
                    check.update({
                        "accessibilityTreeNames": not report["accessibilityTreeUnnamedControls"],
                        "skipLinkKeyboardFirst": report["skipLinkFirstKeyboardTarget"],
                        "skipLinkKeyboardVisible": report["skipLinkVisibleOnFocus"],
                        "skipLinkKeyboardNavigates": report["skipLinkDestination"],
                        "skipLinkKeyboardFocus": report["skipLinkFocusLandsOnMain"],
                        "localeSwitcherLocalizedAndPersistent": all(report["localeSwitch"].values()),
                        "measuredFlatSurfaceTextContrast": report["solidSurfaceContrast"]["failedCount"] == 0,
                        "flatSurfaceCoverage": route == "/" or report["solidSurfaceContrast"]["measured"] > 0,
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
                                         "summary": ({"contrast": report["solidSurfaceContrast"]}
                                                     if name == "measuredFlatSurfaceTextContrast" else report)})
        # Simulate the CSS layout viewport available when a 1280px desktop
        # is viewed at 200% and 400% scale. Keep mobile=False so responsive
        # rules are exercised in desktop emulation, distinct from the 320px
        # phone proof. This does not claim full text zoom conformance.
        for route in ROUTES:
            for width, scale in REFLOW_WIDTHS:
                driver.cdp("Emulation.setDeviceMetricsOverride", {
                    "width": width, "height": 900, "deviceScaleFactor": 1,
                    "mobile": False,
                })
                driver.navigate(f"http://127.0.0.1:{server.server_port}{route}")
                wait_for_route(driver, route)
                report = probe(driver, route, width, 900)
                report["equivalentScalePercent"] = scale
                short = route.strip("/").replace("/", "-") or "home"
                shot = f"reflow-{scale}pct-{short}.png"
                driver.shot(evidence / shot)
                report["screenshot"] = shot
                reflow_results.append(report)
                checks = {
                    "routeRendered": report["complete"] and report["pathname"] == route
                        and report["mainCount"] == 1,
                    "effectiveCssViewport": report["width"] == width,
                    "reflowsWithoutPageHorizontalScroll": report["noOverflow"],
                    "noRemoteResources": not report["remoteResources"],
                    "noBrokenStaticResources": not report["failedStaticAssets"],
                    "noUncaughtScripts": not report["runtimeErrors"],
                }
                if route == "/":
                    checks["landingDemoMounted"] = report["landingFixturePresent"]
                if route == "/conta/":
                    checks["noInventedVerifiedUser"] = not report["accountHasVerifiedUser"]
                if route in NO_SCRIPT_ROUTES[:4]:
                    checks["formsRemainFailClosed"] = not report["exposedAuthForms"] and not report["enabledCredentials"]
                for rule, good in checks.items():
                    if not good:
                        failures.append({"route": route, "viewport": f"reflow-{scale}",
                                         "rule": rule, "summary": report})
        # Verify that disabling JavaScript at document parse time cannot
        # expose identity forms, verified identity or the Web launch. Re-enable
        # only after loading to inspect the inert DOM; deferred scripts must
        # not be replayed.
        driver.cdp("Emulation.setDeviceMetricsOverride", {
            "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
        })
        for route in NO_SCRIPT_ROUTES:
            driver.cdp("Emulation.setScriptExecutionDisabled", {"value": True})
            driver.navigate(f"http://127.0.0.1:{server.server_port}{route}")
            driver.cdp("Emulation.setScriptExecutionDisabled", {"value": False})
            report = no_script_probe(driver)
            name = route.strip("/").replace("/", "-")
            shot = f"noscript-{name}.png"
            driver.shot(evidence / shot)
            report["screenshot"] = shot
            no_script_results.append(report)
            checks = {
                "loaded": report["pathname"] == route and report["hasMain"],
                "visibleNoScriptGuidance": report["noscriptGuidanceVisible"],
                "navigationStillAvailable": report["navigationAvailable"],
                "noAuthFormExposed": not report["authFormsExposed"],
                "noCredentialEntryActivated": not report["enabledAuthControls"],
                "noScriptRuntimeActivated": report["noRuntimeActivated"],
                "noFabricatedAccount": report["accountNotVerified"],
                "noWebLaunch": report["webLaunchUnavailable"],
            }
            for rule, good in checks.items():
                if not good:
                    failures.append({"route": route, "viewport": "noscript",
                                     "rule": rule, "summary": report})
        output = {"schema": "ordax.site-browser-proof/2", "routeCount": len(ROUTES),
                  "viewportCount": len(VIEWPORTS), "checks": len(results),
                  "reflowChecks": len(reflow_results), "noScriptChecks": len(no_script_results),
                  "failures": failures, "results": results,
                  "reflowResults": reflow_results, "noScriptResults": no_script_results}
        (evidence / "report.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if failures:
            raise BrowserProofError(f"{len(failures)} browser checks failed; see report.json; "
                                    + "; ".join(f"{r['route']}@{r['viewport']}:{r['rule']}"
                                      + (":" + json.dumps(r["summary"].get("overflowElements", [])[:6], ensure_ascii=False)
                                         if r["rule"] == "reflowsWithoutPageHorizontalScroll" else "")
                                      + (":" + json.dumps(r["summary"].get("contrast", {}).get("failed", [])[:4], ensure_ascii=False)
                                         if r["rule"] == "measuredFlatSurfaceTextContrast" else "")
                                      for r in failures[:15]))
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
    print(f"SITE_BROWSER_PROOF=PASS routes={output['routeCount']} viewports={output['viewportCount']} checks={output['checks']} reflow={output['reflowChecks']} noscript={output['noScriptChecks']}")


if __name__ == "__main__":
    try:
        main()
    except (BrowserProofError, OSError, ValueError) as error:
        raise SystemExit(f"SITE_BROWSER_PROOF=FAIL {error}")
