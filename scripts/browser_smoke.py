#!/usr/bin/env python3
"""Local, non-deploy browser proof for an already-verified static Site artifact.

Uses Python stdlib + ChromeDriver preinstalled on GitHub's pinned Ubuntu image.
No browser package or OS/Surface checkout is required.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
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
VIEWPORTS = ((1440, 900), (1024, 900), (768, 900), (760, 900),
             (430, 900), (390, 844), (360, 800), (320, 740))
# Touch-first tablets retain a desktop CSS viewport while using coarse input.
# Sample both sides of shared-shell and account-app layout boundaries.
TOUCH_VIEWPORTS = (641, 760, 761, 1100, 1101, 1180, 1181)
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
        # Hold the config fetch after login has loaded to prove legacy bearer
        # fragments are removed BEFORE the first asynchronous network reply.
        if self.path == "/config/public-site.json" and getattr(
                self.server, "hold_config_for_fragment_test", False):
            self.server.fragment_config_started.set()
            self.server.fragment_config_release.wait(timeout=4)
            return super().do_GET()
        # Three synthetic sessions share an email but differ in identity.
        # Usage A (91) is shown, B (44) is delayed, and C (7) must replace
        # both. Only the loopback proof serves these read-only fixtures.
        if getattr(self.server, "same_email_usage_test", False) and self.path in (
                "/auth/session", "/account/usage/mcp"):
            with self.server.same_email_lock:
                if self.path == "/auth/session":
                    self.server.same_email_session_requests += 1
                    attempt = self.server.same_email_session_requests
                else:
                    self.server.same_email_usage_requests += 1
                    attempt = self.server.same_email_usage_requests
            if self.path == "/auth/session":
                payload = {
                    "$schema": "prototype-ordax.public-identity-session/1",
                    "provider": "supabase", "status": "authenticated",
                    "authenticated": True, "subject": "synthetic-owner-" + str(attempt),
                    "email": "same-email@example.test",
                }
            else:
                if attempt == 2:
                    time.sleep(1.05)
                count = {1: 91, 2: 44, 3: 7}.get(attempt, 0)
                payload = {
                    "ok": True, "schema": "ordax.product-mcp-usage/1",
                    "billable": False, "observed_only": True,
                    "coverage": "partial_observational",
                    "collection_active_now": True,
                    "quota": None, "charge": None,
                    "current_month": "2026-10-01",
                    "previous_month": "2026-09-01",
                    "entries": [{"month": "2026-10-01", "tool_name": "local_test",
                                 "tool_calls": count}],
                }
            content = json.dumps(payload).encode("utf-8")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        # Identity JSON attacks are local to this browser proof: a 200 with
        # JSON bytes is not enough if MIME or the byte budget is wrong.
        json_attack = getattr(self.server, "auth_json_attack_for_test", None)
        if self.path == "/auth/session" and json_attack:
            payload = {
                "$schema": "prototype-ordax.public-identity-session/1",
                "provider": "supabase", "status": "authenticated",
                "authenticated": True, "subject": "synthetic-json-attack",
                "email": "untrusted-json@example.test",
            }
            if json_attack == "oversized":
                payload["padding"] = "x" * 270000
            content = json.dumps(payload).encode("utf-8")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain" if json_attack == "wrong-mime"
                                 else "application/json")
                self.send_header("Cache-Control", "no-store")
                # Omitting Content-Length in the oversized case proves the
                # actual streaming cap, not merely a header-size rejection.
                if json_attack != "oversized":
                    self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        # Delayed old anonymous response vs. immediate new unavailability:
        # page revalidation must not resurrect a stale Identity form.
        if self.path == "/auth/session" and getattr(self.server, "auth_session_race_for_test", False):
            with self.server.auth_race_lock:
                self.server.auth_race_requests += 1
                attempt = self.server.auth_race_requests
            if attempt == 1:
                time.sleep(0.8)
                code = 200
                payload = {"$schema": "prototype-ordax.public-identity-session/1",
                           "provider": "supabase", "authenticated": False, "status": "anonymous"}
            else:
                code = 503
                payload = {"error": "service-unavailable"}
            content = json.dumps(payload).encode("utf-8")
            try:
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass  # A superseded fetch is allowed to abort on the client.
            return
        # Redirect-based session forgery exists only in this loopback proof.
        # Even a 200 JSON served at a different same-origin route is not the
        # canonical /auth/session response; the browser must reject it.
        if getattr(self.server, "auth_session_redirect_for_test", False):
            if self.path == "/auth/session":
                self.send_response(302)
                self.send_header("Location", "/__test_redirected_identity.json")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            if self.path == "/__test_redirected_identity.json":
                payload = {
                    "$schema": "prototype-ordax.public-identity-session/1",
                    "provider": "supabase",
                    "status": "authenticated",
                    "authenticated": True,
                    "subject": "synthetic-test-subject",
                    "email": "redirect-attacker@example.test",
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
        # Negative download-contract responses exist only inside this loopback
        # browser proof. Never modify the verified build or publish a fixture.
        catalog_override = getattr(self.server, "catalog_override", None)
        manifest_override = getattr(self.server, "manifest_override", None)
        payload = (catalog_override if self.path == "/releases/catalog.json"
                   else manifest_override if self.path == "/public-site-manifest.json"
                   else None)
        if payload is not None:
            content = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return
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

    def create(self, chrome_binary: str | None = None):
        chrome_options = {"args": [
            "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--window-size=1440,900",
        ]}
        if chrome_binary:
            chrome_options["binary"] = chrome_binary
        response = self.command("POST", "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "chrome",
                "goog:chromeOptions": chrome_options,
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
      const header = $('header.site-header');
      const heroCopy = route === '/' ? $('.hero-copy') : null;
      const heroCopyStyle = heroCopy ? getComputedStyle(heroCopy) : null;
      const landingPhoneEntrance = route !== '/' ? null : (() => {
        const phone = $('.playground .phone-device');
        const animation = phone?.getAnimations().find(item =>
          item.animationName === 'phone-enter');
        if (!phone || !animation) return {checked: false, fits: false};
        const previousTime = animation.currentTime;
        const previousState = animation.playState;
        animation.pause();
        animation.currentTime = 0;
        const rect = phone.getBoundingClientRect();
        const viewportWidth = visualViewport?.width || innerWidth;
        const documentWidth = document.documentElement.scrollWidth;
        const result = {
          checked: true,
          fits: rect.left >= -1 && rect.right <= viewportWidth + 1 &&
            documentWidth <= viewportWidth + 1,
          phoneLeft: Math.round(rect.left * 10) / 10,
          phoneRight: Math.round(rect.right * 10) / 10,
          viewportWidth,
          documentWidth
        };
        if (previousTime !== null) animation.currentTime = previousTime;
        if (previousState === 'running') animation.play();
        else if (previousState === 'finished') animation.finish();
        else animation.pause();
        return result;
      })();
      const headerBrand = header?.querySelector(':scope > .brand') ||
        header?.querySelector(':scope > a:first-child');
      const headerActions = header?.querySelector(':scope > .site-actions');
      const headerNav = header?.querySelector(':scope > .site-nav');
      const navLinksContainer = headerNav?.querySelector(':scope > .site-nav-links');
      const localeSelect = header?.querySelector('[data-public-locale-select]');
      const navToggle = headerNav?.querySelector(':scope > .site-nav-tools > [data-public-nav-toggle]');
      const headerBrandBox = headerBrand?.getBoundingClientRect();
      const headerActionsBox = headerActions?.getBoundingClientRect();
      const localeBox = localeSelect?.getBoundingClientRect();
      const navToggleBox = navToggle?.getBoundingClientRect();
      const mobileHeader = innerWidth <= 760;
      const box = element => {
        if (!element) return null;
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return {
          top: Math.round(rect.top), left: Math.round(rect.left),
          width: Math.round(rect.width), height: Math.round(rect.height),
          display: style.display, visibility: style.visibility, color: style.color,
          background: style.backgroundColor
        };
      };
      const localeSharesNavigationLine = route === '/conta/' || !header ||
        (!!localeBox && (mobileHeader
          ? !!navToggleBox && navToggleBox.width > 0 &&
            Math.abs((navToggleBox.top + navToggleBox.height / 2) -
              (localeBox.top + localeBox.height / 2)) <= 4
          : [...navLinksContainer.querySelectorAll(':scope > a')].some(link => {
          const box = link.getBoundingClientRect();
          return Math.abs((box.top + box.height / 2) - (localeBox.top + localeBox.height / 2)) <= 4;
        })));
      const mobileNavigationDisclosureReady = route === '/conta/' || !header || !mobileHeader ||
        (!!navToggle && navLinksContainer &&
          navToggle.getAttribute('aria-controls') === navLinksContainer.id &&
          navToggle.getAttribute('aria-expanded') === 'false' &&
          headerNav.dataset.expanded === 'false' &&
          getComputedStyle(navLinksContainer).display === 'none');
      const footer = $('footer.site-footer');
      const footerLinks = footer ? [...footer.querySelectorAll('a')] : [];
      const footerBox = footer?.getBoundingClientRect();
      const forms = [...document.querySelectorAll('form.identity-form')];
      const visibleAuthForms = forms.filter(x => !x.hidden);
      const readyControls = forms.flatMap(f => [...f.querySelectorAll('input[type=password],button[type=submit]')]).filter(x => !x.disabled);
      const els = [...document.querySelectorAll('[id]')];
      const ids = els.map(e => e.id);
      const controls = [...document.querySelectorAll('a[href],button,input,select,textarea')].filter(e => {
        const box = e.getBoundingClientRect();
        return box.width > 0 && box.height > 0 && getComputedStyle(e).visibility !== 'hidden';
      });
      const undersizedInteractiveTargets = controls.filter(e => {
        const style = getComputedStyle(e);
        const inlineTextLink = e.matches('a[href]') && style.display === 'inline' && e.closest('p');
        return !e.closest('.playground, [hidden], [aria-hidden="true"], dialog:not([open]), details:not([open])') &&
          !e.disabled && !inlineTextLink &&
          (e.getBoundingClientRect().width < 44 || e.getBoundingClientRect().height < 44);
      }).slice(0, 8).map(e => {
        const rect = e.getBoundingClientRect();
        return {tag: e.tagName.toLowerCase(), text: e.textContent.trim().slice(0, 60),
          width: Math.round(rect.width), height: Math.round(rect.height)};
      });
      const undersizedAAInteractiveTargets = controls.filter(e => {
        const style = getComputedStyle(e);
        const inlineTextLink = e.matches('a[href]') && style.display === 'inline' && e.closest('p');
        return !e.closest('.playground, [hidden], [aria-hidden="true"], dialog:not([open]), details:not([open])') &&
          !e.disabled && !inlineTextLink &&
          (e.getBoundingClientRect().width < 24 || e.getBoundingClientRect().height < 24);
      }).slice(0, 8).map(e => {
        const rect = e.getBoundingClientRect();
        return {tag: e.tagName.toLowerCase(), text: e.textContent.trim().slice(0, 60),
          width: Math.round(rect.width), height: Math.round(rect.height)};
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
        mainH1Count: [...document.querySelectorAll('main h1')].filter(h => !h.closest('.playground, [aria-hidden="true"]')).length,
        landingHeroCopyVisible: !heroCopy || (heroCopyStyle.opacity === '1' &&
          heroCopyStyle.visibility === 'visible' && heroCopyStyle.display !== 'none'),
        landingHeroCopyHasNoEntranceAnimation: !heroCopy || heroCopyStyle.animationName === 'none',
        landingPhoneEntrance,
        skip: !!$('.skip-link[href^="#"]'),
        publicHeaderRegionsReady: route === '/conta/' || !header ||
          (!!headerBrand && !!headerActions && !!headerNav && !!navLinksContainer && !!localeSelect),
        publicHeaderBrandActionsShareRow: route === '/conta/' || !header ||
          (!!headerBrandBox && !!headerActionsBox &&
            Math.abs((headerBrandBox.top + headerBrandBox.height / 2) -
              (headerActionsBox.top + headerActionsBox.height / 2)) <= 6),
        publicHeaderLocaleSharesNavigationLine: localeSharesNavigationLine,
        publicMobileNavigationDisclosureReady: mobileNavigationDisclosureReady,
        publicHeaderLayout: !header ? null : {
          header: box(header), navigation: box(headerNav),
          tools: box(headerNav?.querySelector(':scope > .site-nav-tools')),
          locale: box(localeSelect), toggle: box(navToggle),
          links: box(navLinksContainer), expanded: headerNav?.dataset.expanded
        },
        sharedFooterContract: route === '/conta/'
          ? !footer && !!$('footer.page-footer')
          : !!footer,
        sharedFooterLayout: footer ? getComputedStyle(footer).display : null,
        sharedFooterResponsiveLayout: !footer || getComputedStyle(footer).display ===
          (innerWidth <= 600 ? 'grid' : 'flex'),
        sharedFooterFitsViewport: !footer || (footerBox.left >= -2 && footerBox.right <= innerWidth + 2
          && footer.scrollWidth <= footer.clientWidth + 2),
        sharedFooterLinksHaveComfortableTargets: !footer || footerLinks.every(link =>
          link.getBoundingClientRect().width >= 44 && link.getBoundingClientRect().height >= 44),
        undersizedInteractiveTargets,
        undersizedAAInteractiveTargets,
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


def restore_capture_state(driver: Driver, route: str) -> dict:
    """Remove keyboard-test focus and fragment before saving the normal screenshot."""
    state = driver.run(r"""const expectedRoute = '""" + route + r"""';
      const skipLink = document.querySelector('.skip-link');
      const main = document.querySelector('main#conteudo');
      document.activeElement?.blur();
      if (location.hash) history.replaceState(null, '', location.pathname + location.search);
      window.scrollTo({left: 0, top: 0, behavior: 'instant'});
      return {
        route: location.pathname,
        expectedRoute,
        noSkipLinkFocus: !skipLink || !skipLink.matches(':focus'),
        mainExists: !!main,
        noTestFragment: location.hash === '',
        atTop: window.scrollY === 0
      };""")
    # The skip link animates out for 180ms after blur. Let it clear before the
    # screenshot so the accessibility probe cannot cover the shared brand.
    time.sleep(0.25)
    state["skipLinkHidden"] = driver.run(r"""const link = document.querySelector('.skip-link');
      if (!link) return true;
      const rect = link.getBoundingClientRect();
      return getComputedStyle(link).visibility === 'hidden' || rect.bottom <= 0;""")
    return state


def localization_probe(driver: Driver) -> dict:
    """Exercise the actual language selector, including DOM and locale persistence."""
    return driver.run(r"""return (() => {
      const selector = document.querySelector('[data-public-locale-select]');
      const runtime = window.OrdaXPublicI18n;
      const toggle = document.querySelector('[data-public-nav-toggle]');
      if (!selector || !runtime) return {
        selector: false, english: false, portuguese: false, persistence: false,
        menuEnglish: false, menuPortuguese: false
      };
      const apply = value => {
        selector.value = value;
        selector.dispatchEvent(new Event('change', {bubbles:true}));
        return {
          language: document.documentElement.lang,
          stored: localStorage.getItem('ordax.public.locale'),
          selector: selector.value,
          skip: document.querySelector('.skip-link')?.textContent?.trim(),
          menu: toggle?.querySelector('span')?.textContent?.trim(),
          toggleLabel: toggle?.getAttribute('aria-label'),
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
        persistence: localStorage.getItem('ordax.public.locale') === 'pt-BR',
        menuEnglish: location.pathname === '/conta/' ||
          (english.menu === 'Menu' && english.toggleLabel === 'Toggle primary navigation'),
        menuPortuguese: location.pathname === '/conta/' ||
          (portuguese.menu === 'Menu' && portuguese.toggleLabel === 'Alternar navegação principal')
      };
    })();""")


def mobile_navigation_interaction_probe(driver: Driver) -> dict:
    """Exercise the mobile disclosure, including Escape and focus restoration."""
    return driver.run(r"""return (() => {
      const nav = document.querySelector('.site-header > .site-nav');
      const linksContainer = nav?.querySelector(':scope > .site-nav-links');
      const button = nav?.querySelector(':scope > .site-nav-tools > [data-public-nav-toggle]');
      const links = linksContainer ? [...linksContainer.querySelectorAll(':scope > a')] : [];
      if (!nav || !linksContainer || !button || !links.length) return {
        buttonPresent: false, startsCollapsed: false, opensLinks: false,
        escapeClosesAndRestoresFocus: false
      };
      const startsCollapsed = button.getAttribute('aria-expanded') === 'false' &&
        nav.dataset.expanded === 'false' && getComputedStyle(linksContainer).display === 'none';
      button.focus();
      button.click();
      const opensLinks = button.getAttribute('aria-expanded') === 'true' &&
        nav.dataset.expanded === 'true' && getComputedStyle(linksContainer).display !== 'none' &&
        links.every(link => getComputedStyle(link).display !== 'none');
      links[0].focus();
      links[0].dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
      const escapeClosesAndRestoresFocus = button.getAttribute('aria-expanded') === 'false' &&
        nav.dataset.expanded === 'false' && document.activeElement === button &&
        getComputedStyle(linksContainer).display === 'none';
      return {buttonPresent: true, startsCollapsed, opensLinks, escapeClosesAndRestoresFocus};
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


def reduced_motion_probe(driver: Driver) -> dict:
    """Exercise browser prefers-reduced-motion, not a simulated CSS class."""
    return driver.run(r"""return (() => {
      const active = matchMedia('(prefers-reduced-motion: reduce)').matches;
      const html = getComputedStyle(document.documentElement);
      const tested = [];
      for (const selector of [
        '.skip-link', '.button', '.laptop-device', '.phone-device',
        '.phone-shell', '.auth-card', '.account-main', '.desktop-sidebar',
        '.download-hero-art'
      ]) {
        const el = document.querySelector(selector);
        if (!el) continue;
        const style = getComputedStyle(el);
        const time = value => String(value || '').split(',').some(x =>
          Number.parseFloat(x.trim()) > 0.0001);
        tested.push({
          selector,
          transition: style.transitionDuration,
          animation: style.animationDuration,
          animating: time(style.transitionDuration) || time(style.animationDuration),
        });
      }
      return {
        preferenceMatches: active,
        scrollingIsInstant: html.scrollBehavior === 'auto',
        tested,
        activeMotion: tested.filter(x => x.animating).map(x => x.selector),
      };
    })();""")


def forced_colors_probe(driver: Driver) -> dict:
    """Verify Chrome's native forced-colors mode and a perceivable skip-link focus.

    This is a focused automated regression, not a screen-reader or WCAG audit.
    """
    driver.run("""const skip = document.querySelector('.skip-link[href="#conteudo"]');
      if (skip) skip.focus({preventScroll:true});
      return Boolean(skip);""")
    return driver.run(r"""return (() => {
      const skip = document.querySelector('.skip-link[href="#conteudo"]');
      const style = skip && getComputedStyle(skip);
      const rect = skip && skip.getBoundingClientRect();
      const focused = skip && document.activeElement === skip;
      return {
        preferenceMatches: matchMedia('(forced-colors: active)').matches,
        skipFocused: Boolean(focused),
        skipPerceivable: Boolean(focused && rect && rect.width > 0 && rect.height > 0 &&
          rect.top >= 0 && rect.bottom <= innerHeight &&
          style.visibility === 'visible' && style.display !== 'none'),
        skipFocusIndicator: Boolean(style && style.outlineStyle !== 'none' &&
          parseFloat(style.outlineWidth) >= 2),
        noHorizontalOverflow: document.documentElement.scrollWidth <= innerWidth + 2,
      };
    })();""")


def text_enlargement_probe(driver: Driver) -> dict:
    """200% computed-font-size stress test; not native browser text zoom."""
    return driver.run(r"""return (() => {
      const excluded = '.playground, .sr-only, [hidden], [aria-hidden="true"], script, style';
      const els = [...document.querySelectorAll('body *')].filter(el => {
        if (el.closest(excluded) || el.matches('svg, svg *, img, canvas')) return false;
        const css = getComputedStyle(el);
        if (css.display === 'none' || css.visibility !== 'visible') return false;
        const ownsText = [...el.childNodes].some(n =>
          n.nodeType === Node.TEXT_NODE && n.textContent.trim());
        return ownsText || el.matches('input:not([type="hidden"]), textarea, select');
      });
      const samples = els.map(el => ({el, size: parseFloat(getComputedStyle(el).fontSize)}))
        .filter(x => Number.isFinite(x.size) && x.size > 0);
      for (const {el, size} of samples)
        el.style.setProperty('font-size', (size * 2) + 'px', 'important');
      const wrongSizes = samples.filter(({el, size}) =>
        Math.abs(parseFloat(getComputedStyle(el).fontSize) - size * 2) > 0.25);
      const clippedText = samples.filter(({el}) => {
        const css = getComputedStyle(el), rect = el.getBoundingClientRect();
        if (!rect.width || !rect.height) return false;
        return (/^(hidden|clip)$/.test(css.overflowY) && el.scrollHeight > el.clientHeight + 2) ||
          (/^(hidden|clip)$/.test(css.overflowX) && el.scrollWidth > el.clientWidth + 2);
      }).slice(0, 12).map(({el}) => ({
        tag: el.tagName.toLowerCase(), selector: String(el.className || '').slice(0, 70),
        text: String(el.textContent || el.value || '').trim().slice(0, 70),
        width: el.clientWidth, scrollWidth: el.scrollWidth,
        height: el.clientHeight, scrollHeight: el.scrollHeight
      }));
      const overflowElements = [...document.querySelectorAll('body *')].filter(el => {
        if (el.closest('.playground')) return false;
        const rect = el.getBoundingClientRect(), css = getComputedStyle(el);
        return rect.width > 0 && rect.right > innerWidth + 2 &&
          rect.left < innerWidth && css.display !== 'none' &&
          css.visibility !== 'hidden' && css.position !== 'fixed';
      }).slice(0, 12).map(el => ({
        tag: el.tagName.toLowerCase(), selector: String(el.className || '').slice(0, 85),
        right: Math.round(el.getBoundingClientRect().right)
      }));
      return {
        method: 'computed-font-size-doubling-not-native-browser-zoom',
        scalePercent: 200, scaledTextNodes: samples.length,
        wrongSizes: wrongSizes.length, clippedText,
        width: innerWidth, documentScrollWidth: document.documentElement.scrollWidth,
        noPageHorizontalOverflow: document.documentElement.scrollWidth <= innerWidth + 2,
        overflowElements,
        noUnexpectedRuntimeErrors: !(window.__ordaxPageErrors || []).length
      };
    })();""")


def text_spacing_probe(driver: Driver) -> dict:
    """Apply WCAG 1.4.12 spacing overrides to Site text, then inspect layout.

    Browser DOM stress test, not visual proof or validation of Surface internals.
    """
    return driver.run(r"""return (() => {
      const ignored = '.playground, .sr-only, [hidden], [aria-hidden="true"], script, style';
      const nodes = [...document.querySelectorAll('body *')].filter(el => {
        if (el.closest(ignored) || el.matches('svg, svg *, img, canvas')) return false;
        const css = getComputedStyle(el);
        if (css.display === 'none' || css.visibility !== 'visible') return false;
        return [...el.childNodes].some(node =>
          node.nodeType === Node.TEXT_NODE && node.textContent.trim()) ||
          el.matches('input:not([type="hidden"]), textarea, select');
      });
      const paragraphs = [...document.querySelectorAll('p')].filter(el =>
        !el.closest(ignored) && getComputedStyle(el).display !== 'none' &&
        el.getBoundingClientRect().height > 0);
      for (const el of nodes) {
        el.style.setProperty('line-height', '1.5', 'important');
        el.style.setProperty('letter-spacing', '0.12em', 'important');
        el.style.setProperty('word-spacing', '0.16em', 'important');
      }
      for (const el of paragraphs)
        el.style.setProperty('margin-block-end', '2em', 'important');
      const wrongMetrics = nodes.filter(el => {
        const c = getComputedStyle(el), sz = parseFloat(c.fontSize);
        return !sz || parseFloat(c.lineHeight) + 0.25 < 1.5 * sz ||
          parseFloat(c.letterSpacing) + 0.25 < 0.12 * sz ||
          parseFloat(c.wordSpacing) + 0.25 < 0.16 * sz;
      }).slice(0, 12).map(el => ({
        tag: el.tagName.toLowerCase(), cls: String(el.className || '').slice(0, 65),
        text: String(el.textContent || el.value || '').trim().slice(0, 70),
      }));
      const wrongParagraphMargins = paragraphs.filter(el => {
        const c = getComputedStyle(el);
        return parseFloat(c.marginBottom) + 0.25 < 2 * parseFloat(c.fontSize);
      }).slice(0, 12).map(el => ({
        text: String(el.textContent || '').trim().slice(0, 65),
        margin: getComputedStyle(el).marginBottom,
        fontSize: getComputedStyle(el).fontSize
      }));
      const clippedText = nodes.filter(el => {
        const c = getComputedStyle(el), rect = el.getBoundingClientRect();
        if (!rect.width || !rect.height) return false;
        return (/^(hidden|clip)$/.test(c.overflowY) && el.scrollHeight > el.clientHeight + 2) ||
          (/^(hidden|clip)$/.test(c.overflowX) && el.scrollWidth > el.clientWidth + 2);
      }).slice(0, 12).map(el => ({
        tag: el.tagName.toLowerCase(), cls: String(el.className || '').slice(0, 65),
        text: String(el.textContent || el.value || '').trim().slice(0, 70),
        width: el.clientWidth, scrollWidth: el.scrollWidth,
        height: el.clientHeight, scrollHeight: el.scrollHeight
      }));
      return {
        locale: document.documentElement.lang,
        method: 'dom-wcag-text-spacing-overrides-not-native-text-zoom',
        spacedTextNodes: nodes.length,
        spacedParagraphs: paragraphs.length,
        wrongMetrics, wrongParagraphMargins, clippedText,
        width: innerWidth, documentScrollWidth: document.documentElement.scrollWidth,
        noPageHorizontalOverflow: document.documentElement.scrollWidth <= innerWidth + 2,
        noUnexpectedRuntimeErrors: !(window.__ordaxPageErrors || []).length
      };
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
        mainHasSinglePrimaryHeading: [...document.querySelectorAll('main h1')].filter(h => !h.closest('.playground, [aria-hidden="true"]')).length === 1,
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


def run(root: Path, evidence: Path, chrome_binary: str | None = None) -> dict:
    if not (root / "public-site-manifest.json").is_file():
        raise BrowserProofError("build candidate missing; never browse unpackaged source")
    chrome_binary = (str(Path(chrome_binary).resolve()) if chrome_binary
                     else shutil.which("google-chrome"))
    if (not shutil.which("chromedriver") or not chrome_binary
            or not Path(chrome_binary).is_file()):
        raise BrowserProofError(
            "Chrome + ChromeDriver required; pass --chrome-binary when Chrome is not on PATH")
    evidence.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *a, **k: Handler(*a, root=root, **k),
    )
    server.catalog_override = None
    server.manifest_override = None
    server.auth_session_redirect_for_test = False
    server.auth_json_attack_for_test = None
    server.auth_session_race_for_test = False
    server.auth_race_requests = 0
    server.auth_race_lock = threading.Lock()
    server.same_email_usage_test = False
    server.same_email_session_requests = 0
    server.same_email_usage_requests = 0
    server.same_email_lock = threading.Lock()
    server.hold_config_for_fragment_test = False
    server.fragment_config_started = threading.Event()
    server.fragment_config_release = threading.Event()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    webdriver_port = free_port()
    command = ["chromedriver", f"--port={webdriver_port}", "--allowed-ips=127.0.0.1"]
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    driver = Driver(webdriver_port)
    results = []
    touch_results = []
    reflow_results = []
    text_enlargement_results = []
    text_spacing_results = []
    no_script_results = []
    catalog_failure_results = []
    redirect_identity_results = []
    json_contract_results = []
    identity_race_results = []
    same_email_usage_results = []
    legacy_fragment_results = []
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
        driver.create(chrome_binary)
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
                    driver.cdp("Emulation.setEmulatedMedia", {"features": [
                        {"name": "prefers-reduced-motion", "value": "reduce"}
                    ]})
                    try:
                        report["reducedMotion"] = reduced_motion_probe(driver)
                    finally:
                        driver.cdp("Emulation.setEmulatedMedia", {"features": [
                            {"name": "prefers-reduced-motion", "value": "no-preference"}
                        ]})
                    driver.cdp("Emulation.setEmulatedMedia", {"features": [
                        {"name": "forced-colors", "value": "active"}
                    ]})
                    try:
                        report["forcedColors"] = forced_colors_probe(driver)
                        short = route.strip("/").replace("/", "-") or "home"
                        forced_shot = f"forced-colors-{short}.png"
                        driver.shot(evidence / forced_shot)
                        report["forcedColors"]["screenshot"] = forced_shot
                    finally:
                        driver.cdp("Emulation.setEmulatedMedia", {"features": [
                            {"name": "forced-colors", "value": "none"}
                        ]})
                    report["captureStateRestored"] = restore_capture_state(driver, route)
                short = route.strip("/").replace("/", "-") or "home"
                filename = f"{short}-{width}x{height}.png"
                driver.shot(evidence / filename)
                report.update({"expectedRoute": route, "screenshot": filename})
                if width == 390 and route != "/conta/":
                    report["mobileNavigationInteraction"] = mobile_navigation_interaction_probe(driver)
                results.append(report)
                check = {
                    "loaded": report["complete"] and report["pathname"] == route and report["mainCount"] == 1,
                    "correctLanguage": report["lang"] in ("pt-BR", "en-US"),
                    "namedDocument": bool(report["title"]),
                    "mainHasSinglePrimaryHeading": report["mainH1Count"] == 1,
                    "skipNavigation": report["skip"],
                    "publicHeaderRegionsReady": report["publicHeaderRegionsReady"],
                    "publicHeaderBrandActionsShareRow": report["publicHeaderBrandActionsShareRow"],
                    "publicHeaderLocaleSharesNavigationLine": report["publicHeaderLocaleSharesNavigationLine"],
                    "publicMobileNavigationDisclosureReady": report["publicMobileNavigationDisclosureReady"],
                    "sharedFooterContract": report["sharedFooterContract"],
                    "sharedFooterResponsiveLayout": report["sharedFooterResponsiveLayout"],
                    "sharedFooterFitsViewport": report["sharedFooterFitsViewport"],
                    "sharedFooterLinksHaveComfortableTargets": report["sharedFooterLinksHaveComfortableTargets"],
                    "siteInteractiveTargetsHaveComfortableSize": width > 640 or not report["undersizedInteractiveTargets"],
                    "siteInteractiveTargetsMeetMinimumSize": not report["undersizedAAInteractiveTargets"],
                    "noHorizontalOverflow": report["noOverflow"],
                    "uniqueElementIds": not report["duplicateIds"],
                    "accessibleInteractiveNames": not report["nameless"],
                    "visibleImagesHaveAltAttribute": not report["unlabeledImages"],
                    "noUnexpectedRemoteRequests": not report["remoteResources"],
                    "noBrokenStaticNetworkAssets": not report["failedStaticAssets"],
                    "noUncaughtBrowserErrors": not report["runtimeErrors"],
                }
                if width == 390 and route != "/conta/":
                    check["publicMobileNavigationOpensAndEscapes"] = all(
                        report["mobileNavigationInteraction"].values()
                    )
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
                        "reducedMotionBrowserPreferenceHonored": report["reducedMotion"]["preferenceMatches"]
                          and report["reducedMotion"]["scrollingIsInstant"]
                          and not report["reducedMotion"]["activeMotion"],
                        "nativeForcedColorsAndSkipFocus": all(
                            report["forcedColors"][key] for key in (
                                "preferenceMatches", "skipFocused", "skipPerceivable",
                                "skipFocusIndicator", "noHorizontalOverflow"
                            )
                        ),
                        "visualScreenshotRestoredAfterKeyboardProbe": (
                            report["captureStateRestored"]["route"] == route
                            and report["captureStateRestored"]["expectedRoute"] == route
                            and report["captureStateRestored"]["noSkipLinkFocus"]
                            and report["captureStateRestored"]["skipLinkHidden"]
                            and report["captureStateRestored"]["mainExists"]
                            and report["captureStateRestored"]["noTestFragment"]
                            and report["captureStateRestored"]["atTop"]
                        ),
                    })
                if route in ("/login/", "/cadastro/", "/recuperar/", "/recuperar/nova-senha/"):
                    check.update({"formsFailClosed": not report["exposedAuthForms"] and not report["enabledCredentials"]})
                if route == "/conta/":
                    check.update({"accountShellPresent": report["accountPortal"],
                                  "noInventedVerifiedUser": not report["accountHasVerifiedUser"]})
                if route == "/":
                    check.update({
                        "landingFixturePresent": report["landingFixturePresent"],
                        "landingHeroCopyVisibleOnFirstRender": report["landingHeroCopyVisible"],
                        "landingHeroCopyHasNoEntranceAnimation": report["landingHeroCopyHasNoEntranceAnimation"],
                        "landingPhoneEntranceFitsViewport": report["landingPhoneEntrance"]["checked"]
                          and report["landingPhoneEntrance"]["fits"],
                    })
                for name, success in check.items():
                    if not success:
                        failures.append({"route": route, "viewport": width, "rule": name,
                                         "summary": ({"contrast": report["solidSurfaceContrast"]}
                                                     if name == "measuredFlatSurfaceTextContrast"
                                                     else {"reducedMotion": report["reducedMotion"]}
                                                     if name == "reducedMotionBrowserPreferenceHonored"
                                                     else {"forcedColors": report["forcedColors"]}
                                                     if name == "nativeForcedColorsAndSkipFocus" else report)})
        # Verify the desktop-CSS layouts used by tablets and hybrid touch
        # devices. This exercises any-pointer: coarse independently from the
        # narrow mobile viewport matrix above.
        driver.cdp("Emulation.setTouchEmulationEnabled", {
            "enabled": True, "maxTouchPoints": 1,
        })
        for route in ROUTES:
            for width in TOUCH_VIEWPORTS:
                driver.cdp("Emulation.setDeviceMetricsOverride", {
                    "width": width, "height": 900, "deviceScaleFactor": 1,
                    "mobile": False,
                })
                driver.navigate(f"http://127.0.0.1:{server.server_port}{route}")
                wait_for_route(driver, route)
                report = probe(driver, route, width, 900)
                report["coarsePointer"] = driver.run(
                    "return matchMedia('(any-pointer: coarse)').matches"
                )
                touch_results.append(report)
                checks = {
                    "coarsePointerProfileActive": report["coarsePointer"],
                    "routeRendered": report["complete"] and report["pathname"] == route
                        and report["mainCount"] == 1,
                    "noHorizontalOverflow": report["noOverflow"],
                    "headerBrandActionsShareRow": report["publicHeaderBrandActionsShareRow"],
                    "localeSharesNavigationLine": report["publicHeaderLocaleSharesNavigationLine"],
                    "footerFitsViewport": report["sharedFooterFitsViewport"],
                    "footerLinksHaveComfortableTargets": report["sharedFooterLinksHaveComfortableTargets"],
                    "interactiveTargetsHaveComfortableSize": not report["undersizedInteractiveTargets"],
                }
                if width <= 760 and route != "/conta/":
                    checks["mobileDisclosureReady"] = report["publicMobileNavigationDisclosureReady"]
                if route == "/conta/":
                    checks["accountShellPresent"] = report["accountPortal"]
                    checks["noInventedVerifiedUser"] = not report["accountHasVerifiedUser"]
                if route == "/":
                    checks["landingPhoneEntranceFitsViewport"] = (
                        report["landingPhoneEntrance"]["checked"]
                        and report["landingPhoneEntrance"]["fits"]
                    )
                for name, success in checks.items():
                    if not success:
                        failures.append({"route": route, "viewport": f"touch-{width}",
                                         "rule": name, "summary": report})
        driver.cdp("Emulation.setTouchEmulationEnabled", {"enabled": False})
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
        # Stress test computed font-size 200% on the Site-owned presentation.
        # This is not Chrome's native text-only zoom and does not alter source.
        for route in ROUTES:
            driver.cdp("Emulation.setDeviceMetricsOverride", {
                "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
            })
            driver.navigate(f"http://127.0.0.1:{server.server_port}{route}")
            wait_for_route(driver, route)
            report = text_enlargement_probe(driver)
            report["route"] = route
            short = route.strip("/").replace("/", "-") or "home"
            shot = f"text-200pct-{short}.png"
            driver.shot(evidence / shot)
            report["screenshot"] = shot
            text_enlargement_results.append(report)
            checks = {
                "textActuallyDoubled": report["scaledTextNodes"] > 0 and report["wrongSizes"] == 0,
                "textDoesNotClip": not report["clippedText"],
                "textDoesNotCausePageOverflow": report["noPageHorizontalOverflow"],
                "noUncaughtScripts": report["noUnexpectedRuntimeErrors"],
            }
            for rule, passed in checks.items():
                if not passed:
                    failures.append({"route": route, "viewport": "text-200pct",
                                     "rule": rule, "summary": report})
        # WCAG 1.4.12 spacing stress at 390px in both supported locales.
        # Overrides exist only in the test DOM; keep external Surface immutable.
        for route in ROUTES:
            for locale in ("pt-BR", "en-US"):
                driver.cdp("Emulation.setDeviceMetricsOverride", {
                    "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
                })
                driver.navigate(f"http://127.0.0.1:{server.server_port}{route}")
                wait_for_route(driver, route)
                selected_locale = driver.run(
                    """const selector = document.querySelector('[data-public-locale-select]');
                    if (!selector) return false;
                    selector.value = '""" + locale + """';
                    selector.dispatchEvent(new Event('change', {bubbles: true}));
                    return selector.value === document.documentElement.lang
                      && selector.value === '""" + locale + """';"""
                )
                report = text_spacing_probe(driver)
                report.update({"route": route, "expectedLocale": locale, "localeChanged": selected_locale})
                short = route.strip("/").replace("/", "-") or "home"
                shot = f"spacing-{locale}-{short}.png"
                driver.shot(evidence / shot)
                report["screenshot"] = shot
                text_spacing_results.append(report)
                checks = {
                    "localeApplied": selected_locale and report["locale"] == locale,
                    "textActuallySpaced": report["spacedTextNodes"] > 0,
                    "metricsMeet1_4_12": not report["wrongMetrics"] and not report["wrongParagraphMargins"],
                    "noTextClipping": not report["clippedText"],
                    "noPageHorizontalOverflow": report["noPageHorizontalOverflow"],
                    "noUncaughtScripts": report["noUnexpectedRuntimeErrors"],
                }
                for rule, passed in checks.items():
                    if not passed:
                        failures.append({"route": route, "viewport": f"spacing-{locale}",
                                         "rule": rule, "summary": report})
        # Exercise poisoned catalogs through the REAL Site browser runtime
        # without changing the pinned candidate or invoking any publisher.
        demo_id = "1" * 40
        artifact = lambda path: {"href": path, "sha256": "a" * 64, "size": 123}
        demo_target = {"id": "unit-test-only", "label": "Never published",
                       **artifact("/releases/offline-test-only.img")}
        demo_release = {
            "release_id": demo_id, "source_commit": demo_id,
            "version": "offline-test-only", "channel": "test",
            "published_at": "2026-10-24",
            "targets": [demo_target],
            "compliance": {
                "sbom": artifact("/compliance/test-sbom.json"),
                "third_party_notices": artifact("/compliance/test-notices.txt"),
                "source_bundle": artifact("/compliance/test-sources.tar.gz"),
            },
        }
        invalid_catalogs = [
            ("empty-with-releases", {"$schema": "prototype-ordax.public-release-catalog/1",
                                      "status": "empty", "releases": [demo_release]}),
            ("repeated-target-id", {"$schema": "prototype-ordax.public-release-catalog/1",
                                     "status": "ready",
                                     "releases": [{**demo_release,
                                                   "targets": [demo_target, demo_target]}]}),
            ("encoded-traversal", {"$schema": "prototype-ordax.public-release-catalog/1",
                                    "status": "ready",
                                    "releases": [{**demo_release,
                                                  "targets": [{**demo_target, "href":
                                                    "/releases/%2e%2e/auth/login"}]}]}),
            # This one is structurally valid. It must STILL fail because the
            # immutable CI bundle authorizes only the original empty catalog.
            ("valid-ready-but-unattested", {
                "$schema": "prototype-ordax.public-release-catalog/1",
                "status": "ready", "releases": [demo_release],
            }),
            ("empty-with-unauthorized-field", {
                "$schema": "prototype-ordax.public-release-catalog/1",
                "status": "empty", "releases": [], "injected": True,
            }),
        ]
        # A forged ready catalog AND a matching, self-authored manifest are
        # still unauthorized. Both responses come only from this loopback
        # test handler: a matching digest is not a publisher signature.
        actual_manifest = json.loads((root / "public-site-manifest.json").read_text("utf-8"))
        valid_ready = {"$schema": "prototype-ordax.public-release-catalog/1",
                       "status": "ready", "releases": [demo_release]}
        ready_bytes = json.dumps(valid_ready, separators=(",", ":")).encode("utf-8")
        self_attested = json.loads(json.dumps(actual_manifest))
        self_attested["catalog_status"] = "ready"
        self_attested["publications_sha256"] = "a" * 64
        for record in self_attested["files"]:
            if record["path"] == "releases/catalog.json":
                record["size"] = len(ready_bytes)
                record["sha256"] = hashlib.sha256(ready_bytes).hexdigest()
        invalid_catalogs.append(("forged-catalog-and-manifest", valid_ready))
        for scenario, payload in invalid_catalogs:
            server.catalog_override = payload
            server.manifest_override = (
                self_attested if scenario == "forged-catalog-and-manifest" else None
            )
            try:
                driver.cdp("Emulation.setDeviceMetricsOverride", {
                    "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
                })
                driver.navigate(f"http://127.0.0.1:{server.server_port}/download/")
                state = {}
                for _ in range(45):
                    state = driver.run("""const status = document.querySelector('[data-download-status] strong');
                    const expected = window.OrdaXPublicI18n?.t('download.error.title');
                    return {
                      errorState: Boolean(status && expected && status.textContent === expected),
                      visibleReleaseLinks: document.querySelectorAll('[data-release-list] a[href]').length,
                      runtimeErrors: window.__ordaxPageErrors || []
                    };""")
                    if state["errorState"]:
                        break
                    time.sleep(0.1)
                state["scenario"] = scenario
                catalog_failure_results.append(state)
                if not state["errorState"] or state["visibleReleaseLinks"] or state["runtimeErrors"]:
                    failures.append({"route": "/download/", "viewport": "poisoned-catalog",
                                     "rule": scenario, "summary": state})
            finally:
                server.catalog_override = None
                server.manifest_override = None
        # A redirected 200 with plausible authenticated JSON must not grant
        # even a verified *visual* account state. Test at the existing browser
        # entry point rather than introducing a second Identity simulator.
        for scenario in ("redirect", "oversized", "wrong-mime"):
            server.auth_session_redirect_for_test = scenario == "redirect"
            server.auth_json_attack_for_test = scenario if scenario != "redirect" else None
            try:
                driver.navigate(f"http://127.0.0.1:{server.server_port}/conta/")
                report = {}
                for _ in range(45):
                    report = driver.run("""return (() => {
                      const panel = document.getElementById('account-session');
                      const poisoned = ['redirect-attacker@example.test', 'untrusted-json@example.test'];
                      const hasPoison = text => poisoned.some(email => text.includes(email));
                      return {
                        status: panel?.dataset?.status || null,
                        hasAttackerEmail: hasPoison(document.body.textContent),
                        hasVerifiedEmail: [...document.querySelectorAll('.verified-email')]
                          .some(node => hasPoison(node.textContent)),
                        errors: window.__ordaxPageErrors || []
                      };
                    })();""")
                    if report["status"] == "unavailable":
                        break
                    time.sleep(0.1)
                report["scenario"] = scenario
                (redirect_identity_results if scenario == "redirect" else json_contract_results).append(report)
                if report["status"] != "unavailable" or report["hasAttackerEmail"] or report["hasVerifiedEmail"] or report["errors"]:
                    failures.append({"route": "/conta/", "viewport": "untrusted-identity-json",
                                     "rule": "reject-" + scenario, "summary": report})
            finally:
                server.auth_session_redirect_for_test = False
                server.auth_json_attack_for_test = None
        # The old /auth/session GET deliberately returns after a newer refresh
        # has failed. The older 200 must not reactivate a login form even for
        # a moment after the 503 was accepted by the current generation.
        server.auth_session_race_for_test = True
        with server.auth_race_lock:
            server.auth_race_requests = 0
        try:
            driver.navigate(f"http://127.0.0.1:{server.server_port}/login/")
            for _ in range(40):
                with server.auth_race_lock:
                    count = server.auth_race_requests
                if count >= 1:
                    break
                time.sleep(0.05)
            if count < 1:
                failures.append({"route": "/login/", "viewport": "session-race",
                                 "rule": "first-session-request-not-seen"})
            else:
                driver.run("""void window.OrdaXPublicAccount.refreshSession(); return true;""")
                for _ in range(40):
                    with server.auth_race_lock:
                        count = server.auth_race_requests
                    if count >= 2:
                        break
                    time.sleep(0.05)
                # Let both concurrent requests resolve and inspect the final
                # state. No credentials or Turnstile provider are invoked.
                time.sleep(1.05)
                report = driver.run("""return (() => {
                  const form = document.querySelector('[data-identity-form]');
                  const state = document.querySelector('[data-identity-state]');
                  return {
                    status: state?.dataset?.status || null,
                    hidden: form?.hidden === true,
                    activeAction: form?.hasAttribute('action') || false,
                    enabledControls: [...(form?.querySelectorAll('input, button') || [])]
                      .filter(control => !control.disabled).length,
                    ready: document.body.dataset.identityReady,
                    errors: window.__ordaxPageErrors || []
                  };
                })();""")
                report["scenario"] = "stale-anonymous-reply-after-session-refresh"
                report["sessionRequests"] = count
                identity_race_results.append(report)
                if count < 2 or report["status"] != "unavailable" or not report["hidden"] or report["activeAction"] or report["enabledControls"] or report["ready"] != "false" or report["errors"]:
                    failures.append({"route": "/login/", "viewport": "session-race",
                                     "rule": "old-session-result-reactivated-form", "summary": report})
        finally:
            server.auth_session_race_for_test = False
        # Changing verified session with the SAME email must clear usage A
        # instantly; an older B request may never override the newer C data.
        server.same_email_usage_test = True
        with server.same_email_lock:
            server.same_email_session_requests = 0
            server.same_email_usage_requests = 0
        try:
            driver.navigate(f"http://127.0.0.1:{server.server_port}/conta/#consumo")
            def usage_probe():
                return driver.run("""return (() => ({
                  session: document.getElementById('account-session')?.dataset?.status,
                  measurement: document.querySelector('.usage-mcp-panel .billing-large')?.textContent?.trim() || '',
                  email: document.querySelector('#account-session .session-email')?.textContent || '',
                  errors: window.__ordaxPageErrors || []
                }))();""")
            initial = {}
            for _ in range(60):
                initial = usage_probe()
                if initial["measurement"] == "91":
                    break
                time.sleep(0.1)
            if initial.get("measurement") != "91":
                failures.append({"route": "/conta/#consumo", "viewport": "same-email-usage",
                                 "rule": "first-observed-session-not-loaded", "summary": initial})
            else:
                driver.run("""void window.OrdaXPublicAccount.refreshSession(); return true;""")
                cleared = usage_probe()
                for _ in range(40):
                    with server.same_email_lock:
                        b_started = server.same_email_usage_requests >= 2
                    if b_started:
                        break
                    time.sleep(0.05)
                driver.run("""void window.OrdaXPublicAccount.refreshSession(); return true;""")
                final = {}
                for _ in range(50):
                    final = usage_probe()
                    if final["measurement"] == "7":
                        break
                    time.sleep(0.1)
                time.sleep(1.2)  # Delayed B (44) must not replace current C (7).
                after_delayed = usage_probe()
                with server.same_email_lock:
                    counts = (server.same_email_session_requests,
                              server.same_email_usage_requests)
                report = {"scenario": "same-email-different-sessions",
                          "initial": initial, "afterRefresh": cleared,
                          "afterCurrent": final, "afterDelayedOldResponse": after_delayed,
                          "sessionAndUsageRequests": counts}
                same_email_usage_results.append(report)
                if (not b_started or counts[0] < 3 or counts[1] < 3
                    or cleared["measurement"] == "91"
                    or final["measurement"] != "7"
                    or after_delayed["measurement"] != "7"
                    or after_delayed["email"] != "same-email@example.test"
                    or after_delayed["session"] != "authenticated"
                    or after_delayed["errors"]):
                    failures.append({"route": "/conta/#consumo", "viewport": "same-email-usage",
                                     "rule": "session-usage-cache-crossed-boundary", "summary": report})
        finally:
            server.same_email_usage_test = False
        # A historical hosted-identity fragment must disappear before the
        # Site receives even its normal public runtime config. No parsing,
        # storing or token exchange is allowed; the token is synthetic.
        server.fragment_config_started.clear()
        server.fragment_config_release.clear()
        server.hold_config_for_fragment_test = True
        try:
            driver.navigate(f"http://127.0.0.1:{server.server_port}/login/"
                            "#access_token=synthetic-local-proof&token_type=bearer")
            config_started = server.fragment_config_started.wait(timeout=1.5)
            report = driver.run("""return (() => {
              const form = document.querySelector('[data-identity-form]');
              return {
                hashGone: window.location.hash === '',
                tokenNotInAddress: !window.location.href.includes('synthetic-local-proof'),
                formInactive: !form || form.hidden || !form.hasAttribute('action'),
                errors: window.__ordaxPageErrors || []
              };
            })();""")
            report["scenario"] = "legacy-fragment-before-config"
            report["configFetchStarted"] = config_started
            report["configStillHeld"] = not server.fragment_config_release.is_set()
            legacy_fragment_results.append(report)
            if (not all((report["hashGone"], report["tokenNotInAddress"],
                         report["formInactive"], report["configFetchStarted"],
                         report["configStillHeld"])) or report["errors"]):
                failures.append({"route": "/login/", "viewport": "legacy-bearer-fragment",
                                 "rule": "fragment-not-cleared-before-config", "summary": report})
        finally:
            server.fragment_config_release.set()
            server.hold_config_for_fragment_test = False
        # Restore the default language to keep the no-JavaScript checks independent.
        driver.run("""localStorage.setItem('ordax.public.locale', 'pt-BR'); return true;""")
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
                "mainHasSinglePrimaryHeading": report["mainHasSinglePrimaryHeading"],
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
                  "touchResponsiveChecks": len(touch_results),
                  "reflowChecks": len(reflow_results), "textEnlargementChecks": len(text_enlargement_results),
                  "textSpacingChecks": len(text_spacing_results),
                  "noScriptChecks": len(no_script_results),
                  "catalogFailureChecks": len(catalog_failure_results),
                  "redirectIdentityChecks": len(redirect_identity_results),
                  "jsonContractChecks": len(json_contract_results),
                  "identityRaceChecks": len(identity_race_results),
                  "sameEmailUsageChecks": len(same_email_usage_results),
                  "legacyFragmentChecks": len(legacy_fragment_results),
                  "failures": failures, "results": results,
                  "touchResults": touch_results,
                  "reflowResults": reflow_results, "textEnlargementResults": text_enlargement_results,
                  "textSpacingResults": text_spacing_results,
                  "noScriptResults": no_script_results,
                  "catalogFailureResults": catalog_failure_results,
                  "redirectIdentityResults": redirect_identity_results,
                  "jsonContractResults": json_contract_results,
                  "identityRaceResults": identity_race_results,
                  "sameEmailUsageResults": same_email_usage_results,
                  "legacyFragmentResults": legacy_fragment_results}
        (evidence / "report.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if failures:
            raise BrowserProofError(f"{len(failures)} browser checks failed; see report.json; "
                                    + "; ".join(f"{r['route']}@{r['viewport']}:{r['rule']}"
                                      + (":" + json.dumps(r["summary"].get("overflowElements", [])[:6], ensure_ascii=False)
                                         if r["rule"] == "reflowsWithoutPageHorizontalScroll" else "")
                                      + (":" + json.dumps(r["summary"].get("contrast", {}).get("failed", [])[:4], ensure_ascii=False)
                                         if r["rule"] == "measuredFlatSurfaceTextContrast" else "")
                                      + (":" + json.dumps(r["summary"].get("reducedMotion", {}), ensure_ascii=False)
                                         if r["rule"] == "reducedMotionBrowserPreferenceHonored" else "")
                                      + (":" + json.dumps(r["summary"].get("forcedColors", {}), ensure_ascii=False)
                                         if r["rule"] == "nativeForcedColorsAndSkipFocus" else "")
                                      + (":" + json.dumps({
                                           "clippedText":r["summary"].get("clippedText", []),
                                           "overflowElements":r["summary"].get("overflowElements", []),
                                           "documentScrollWidth":r["summary"].get("documentScrollWidth", 0)
                                         }, ensure_ascii=False)
                                         if r["viewport"] == "text-200pct" else "")
                                      + (":" + json.dumps({
                                           "wrongMetrics":r["summary"].get("wrongMetrics", []),
                                           "wrongParagraphMargins":r["summary"].get("wrongParagraphMargins", []),
                                           "clippedText":r["summary"].get("clippedText", []),
                                           "documentScrollWidth":r["summary"].get("documentScrollWidth", 0)
                                         }, ensure_ascii=False)
                                         if str(r["viewport"]).startswith("spacing-") else "")
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
    parser.add_argument(
        "--chrome-binary",
        help="Path to Chrome/Chromium when it is not named google-chrome on PATH",
    )
    args = parser.parse_args()
    output = run(Path(args.out).resolve(), Path(args.evidence).resolve(), args.chrome_binary)
    print(f"SITE_BROWSER_PROOF=PASS routes={output['routeCount']} viewports={output['viewportCount']} checks={output['checks']} touch={output['touchResponsiveChecks']} reflow={output['reflowChecks']} text200={output['textEnlargementChecks']} spacing={output['textSpacingChecks']} noscript={output['noScriptChecks']} catalogReject={output['catalogFailureChecks']} redirectIdentity={output['redirectIdentityChecks']} jsonContract={output['jsonContractChecks']} identityRace={output['identityRaceChecks']} usageSession={output['sameEmailUsageChecks']} fragmentScrub={output['legacyFragmentChecks']}")


if __name__ == "__main__":
    try:
        main()
    except (BrowserProofError, OSError, ValueError) as error:
        raise SystemExit(f"SITE_BROWSER_PROOF=FAIL {error}")
