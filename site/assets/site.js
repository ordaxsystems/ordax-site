(() => {
  "use strict";

  const CONFIG_PATH = "/config/public-site.json";
  const CONFIG_SCHEMA = "prototype-ordax.public-site-runtime/1";
  const CATALOG_SCHEMA = "prototype-ordax.public-release-catalog/1";
  const REGISTRATION_POLICY_SCHEMA = "prototype-ordax.registration-legal-policy/1";
  const TURNSTILE_RUNTIME_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
  const TURNSTILE_ACTION = "ordax-account";
  const TURNSTILE_PROTECTED_KINDS = new Set(["login", "register", "recover"]);
  const i18n = window.OrdaXPublicI18n;
  if (!i18n || i18n.schema !== "prototype-ordax.public-site-localization-runtime/1") {
    throw new Error("public-site-localization-runtime-missing");
  }
  const t = (messageId, variables) => i18n.t(messageId, variables);

  function sameOriginPath(value, method = "GET") {
    // The central selection POST has no query; its GET sibling must carry
    // exactly one OAuth client ID. Keep this distinction at the URL gate.
    if (value === "/account/mcp/central-selections" && method === "POST") return true;
    if (value === "/account/mcp/project-onboarding/projects") {
      return method === "POST";
    }
    // Only the exact Owner device and OAuth-client reads accept a UUID query.
    // Never allow arbitrary parameters, URL normalization or other Identity routes.
    if (typeof value === "string" &&
        /^[/]account[/]mcp[/](?:(?:authority|project-onboarding)[?]device_id|central-(?:targets|selections)[?]client_id)=[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value)) {
      return true;
    }
    // These admin reads require exactly one scoped UUID, not a bare route.
    if (["/account/mcp/authority","/account/mcp/project-onboarding",
      "/account/mcp/central-targets","/account/mcp/central-selections"].includes(value)) return false;
    // Keep browser links aligned with the Site catalog's canonical path gate.
    // Disallow encoded separators/dots, traversals and URL normalization aliases.
    return (
      typeof value === "string" &&
      /^\/[A-Za-z0-9._~/-]+$/.test(value) &&
      !value.includes("//") &&
      !value.split("/").some(part => part === "." || part === "..")
    );
  }

  // Eligibility is shared by form rendering and local preview navigation.
  // These are presentation routes only; /auth endpoints are never rewritten.
  const IDENTITY_PREVIEW_PATHS = new Set([
    "/login/", "/cadastro/", "/recuperar/", "/recuperar/nova-senha/",
  ]);
  function isIdentityLayoutPreview() {
    return document.body?.classList?.contains?.("account-ui")
      && IDENTITY_PREVIEW_PATHS.has(window.location.pathname)
      && ["127.0.0.1", "localhost", "[::1]"].includes(window.location.hostname)
      && new URLSearchParams(window.location.search).get("preview") === "layout";
  }

  const MAX_PUBLIC_JSON_BYTES = 256 * 1024;
  async function readJsonBytes(response, maxBytes = MAX_PUBLIC_JSON_BYTES) {
    // One bounded JSON transport for Identity/config/policy and catalog.
    // Never allocate a server-chosen body before checking its size.
    const mime = response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase();
    const length = response.headers.get("Content-Length");
    if (mime !== "application/json" ||
        !Number.isSafeInteger(maxBytes) || maxBytes < 0 ||
        (length !== null && (!/^\d+$/.test(length) || Number(length) > maxBytes)) ||
        !response.body?.getReader) {
      throw new Error("invalid-public-json-response");
    }
    const buffer = new Uint8Array(maxBytes);
    const reader = response.body.getReader();
    let received = 0;
    try {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!(value instanceof Uint8Array) || received + value.length > maxBytes) {
          await reader.cancel();
          throw new Error("public-json-too-large");
        }
        buffer.set(value, received);
        received += value.length;
      }
    } finally {
      reader.releaseLock();
    }
    return buffer.subarray(0, received);
  }

  function parseJsonBytes(bytes) {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  }

  async function loadJson(path, signal, {
    maxBytes = MAX_PUBLIC_JSON_BYTES,
    credentials = "same-origin",
    cache = "no-store",
    method = "GET",
    jsonBody,
  } = {}) {
    // API contracts belong to their exact same-origin endpoint. A redirected
    // 200 (even to another same-origin route) cannot establish Identity or
    // legal-policy readiness; never follow redirects or accept alias responses.
    if (!sameOriginPath(path, method)) throw new Error("api-path-invalid");
    if (method !== "GET" && (method !== "POST" || ![
      "/account/mcp/revoke", "/account/mcp/central-selections",
    ].includes(path))) {
      throw new Error("api-method-not-allowed");
    }
    if (method === "GET" && jsonBody !== undefined) throw new Error("api-get-body-not-allowed");
    // A stalled HTTP response or streaming body must not keep public forms,
    // product availability or demo status in "checking" indefinitely.
    // The same request deadline applies to every JSON consumer, and an
    // external cancellation still propagates without owning a second timer.
    const deadline = new AbortController();
    const timeoutId = setTimeout(() => deadline.abort(), 10000);
    const onAbort = () => deadline.abort();
    if (signal?.aborted) deadline.abort();
    else signal?.addEventListener("abort", onAbort, { once: true });
    try {
      const response = await fetch(path, {
        method,
        credentials,
        cache,
        redirect: "error",
        headers: method === "POST"
          ? { Accept: "application/json", "Content-Type": "application/json" }
          : { Accept: "application/json" },
        ...(method === "POST" ? { body: JSON.stringify(jsonBody) } : {}),
        signal: deadline.signal,
      });
      if (!response.ok || response.redirected ||
          response.url !== new URL(path, window.location.origin).href) {
        throw new Error("resource-unavailable");
      }
      return parseJsonBytes(await readJsonBytes(response, maxBytes));
    } finally {
      clearTimeout(timeoutId);
      signal?.removeEventListener("abort", onAbort);
    }
  }

  // A single bounded JSON loader owns the MIME, redirect, and size checks.
  // Static presentation fixtures use it without credentials or Identity state.
  window.OrdaXPublicJsonTransport = Object.freeze({
    loadStatic: (path, maxBytes) => loadJson(path, undefined, {
      maxBytes, credentials: "omit", cache: "no-cache",
    }),
  });

  async function loadConfig() {
    const config = await loadJson(CONFIG_PATH);
    if (!config || config.$schema !== CONFIG_SCHEMA) {
      throw new Error("invalid-public-site-config");
    }
    return config;
  }

  function validHttpsDocumentUrl(value) {
    if (typeof value !== "string") return false;
    try {
      const url = new URL(value);
      const raw = value.trim();
      const schemeBoundary = raw.indexOf("://");
      const authority = schemeBoundary > 0
        ? raw.slice(schemeBoundary + 3).split("/", 1)[0]
        : "";
      return (
        url.protocol === "https:"
        && schemeBoundary > 0
        && authority.length > 0
        && !authority.includes("@")
        && !url.search
        && !url.hash
      );
    } catch {
      return false;
    }
  }

  // Only the historical policy can use mutable presentation pages. Every
  // new consent version must point to its byte-stable publication snapshot.
  function canonicalLegalDocument(value, path, version) {
    if (!validHttpsDocumentUrl(value)
        || typeof version !== "string"
        || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(version)) return false;
    try {
      const url = new URL(value);
      const expected = version === "2026.10.09"
        ? path : `/legal/${version}${path}`;
      return url.origin === window.location.origin && url.pathname === expected;
    } catch {
      return false;
    }
  }

  function validRegistrationDocument(value, path) {
    return (
      value
      && typeof value === "object"
      && typeof value.version === "string"
      && /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(value.version)
      && typeof value.effectiveDate === "string"
      && /^\d{4}-\d{2}-\d{2}$/.test(value.effectiveDate)
      && validSha256(value.sha256)
      && canonicalLegalDocument(value.url, path, value.version)
    );
  }

  function validRegistrationPolicy(value) {
    return (
      value
      && value.$schema === REGISTRATION_POLICY_SCHEMA
      && value.active === true
      && value.registrationEnabled === true
      && typeof value.policyId === "string"
      && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.policyId)
      && validRegistrationDocument(value.privacy, "/privacidade/")
      && validRegistrationDocument(value.terms, "/termos/")
    );
  }

  // The server owns immutable consent hashes. Never offer new consent to a
  // document whose currently published bytes no longer match that policy.
  async function verifyPublishedRegistrationDocuments(policy) {
    if (!validRegistrationPolicy(policy) || !globalThis.crypto?.subtle) return false;
    const maxBytes = 2 * 1024 * 1024;
    for (const [documentInfo, route] of [
      [policy.privacy, "/privacidade/"],
      [policy.terms, "/termos/"],
    ]) {
      if (!canonicalLegalDocument(documentInfo.url, route, documentInfo.version)) return false;
      const response = await fetch(documentInfo.url, {
        method: "GET",
        credentials: "omit",
        cache: "no-store",
        redirect: "error",
        headers: { Accept: "text/html" },
      });
      if (!response.ok || response.status !== 200 || response.url !== documentInfo.url
          || response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase() !== "text/html"
          || !response.body) return false;
      const advertisedSize = response.headers.get("Content-Length");
      if (advertisedSize !== null && (!/^\d+$/.test(advertisedSize) || Number(advertisedSize) > maxBytes)) {
        return false;
      }
      const reader = response.body.getReader();
      const chunks = [];
      let bytesRead = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (!(value instanceof Uint8Array)) return false;
          bytesRead += value.byteLength;
          if (bytesRead > maxBytes) {
            await reader.cancel();
            return false;
          }
          chunks.push(value);
        }
      } finally {
        reader.releaseLock();
      }
      const bytes = new Uint8Array(bytesRead);
      let offset = 0;
      for (const chunk of chunks) {
        bytes.set(chunk, offset);
        offset += chunk.byteLength;
      }
      const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
      const hex = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
      if (hex !== documentInfo.sha256) return false;
    }
    return true;
  }

  function renderRegistrationPolicy(form, policy) {
    const host = form.querySelector("[data-registration-legal]");
    if (!host) return false;
    if (!validRegistrationPolicy(policy)) {
      host.hidden = true;
      return false;
    }
    const privacy = host.querySelector("[data-registration-privacy]");
    const privacyMeta = host.querySelector("[data-registration-privacy-meta]");
    const terms = host.querySelector("[data-registration-terms]");
    const termsMeta = host.querySelector("[data-registration-terms-meta]");
    if (!privacy || !privacyMeta || !terms || !termsMeta) {
      host.hidden = true;
      return false;
    }
    privacy.href = policy.privacy.url;
    privacyMeta.textContent = `v${policy.privacy.version} · ${policy.privacy.effectiveDate}`;
    terms.href = policy.terms.url;
    termsMeta.textContent = `v${policy.terms.version} · ${policy.terms.effectiveDate}`;
    host.hidden = false;
    return true;
  }

  function validTurnstileSitekey(value) {
    return typeof value === "string" && /^0x[A-Za-z0-9_-]{20,80}$/.test(value);
  }

  let turnstileLoader = null;
  function loadTurnstileRuntime() {
    if (
      window.turnstile
      && typeof window.turnstile.render === "function"
    ) {
      return Promise.resolve(window.turnstile);
    }
    if (turnstileLoader) return turnstileLoader;
    turnstileLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = TURNSTILE_RUNTIME_URL;
      script.async = true;
      script.defer = true;
      script.referrerPolicy = "no-referrer";
      script.onload = () => {
        if (window.turnstile && typeof window.turnstile.render === "function") {
          resolve(window.turnstile);
        } else {
          reject(new Error("turnstile-runtime-invalid"));
        }
      };
      script.onerror = () => reject(new Error("turnstile-runtime-unavailable"));
      document.head.append(script);
    });
    return turnstileLoader;
  }

  let activeTurnstile = null;
  function removeTurnstile() {
    if (!activeTurnstile) return;
    const { runtime, widget } = activeTurnstile;
    activeTurnstile = null;
    try { runtime.remove?.(widget); } catch { /* Already detached. */ }
  }

  async function armTurnstile(form, sitekey, isCurrent) {
    const host = form.querySelector("[data-turnstile]");
    const submit = form.querySelector('button[type="submit"]');
    if (!host || !submit || !validTurnstileSitekey(sitekey)) return false;
    submit.disabled = true;
    try {
      const runtime = await loadTurnstileRuntime();
      if (!isCurrent()) return false;
      const widget = runtime.render(host, {
        sitekey,
        action: TURNSTILE_ACTION,
        theme: "auto",
        callback(token) {
          submit.disabled = !isCurrent() || typeof token !== "string" || token.length < 1;
        },
        "expired-callback"() {
          submit.disabled = true;
        },
        "error-callback"() {
          submit.disabled = true;
        },
      });
      activeTurnstile = { runtime, widget };
      return true;
    } catch {
      submit.disabled = true;
      return false;
    }
  }

  function identityCopy(kind, available) {
    const copy = {
      login: {
        ready: ["identity.login.ready.title", "identity.login.ready.detail"],
        gated: ["identity.login.gated.title", "identity.login.gated.detail"],
      },
      register: {
        ready: ["identity.register.ready.title", "identity.register.ready.detail"],
        gated: ["identity.register.gated.title", "identity.register.gated.detail"],
      },
      recover: {
        ready: ["identity.recover.ready.title", "identity.recover.ready.detail"],
        gated: ["identity.recover.gated.title", "identity.recover.gated.detail"],
      },
      "recover-complete": {
        ready: ["identity.recoverComplete.ready.title", "identity.recoverComplete.ready.detail"],
        gated: ["identity.recoverComplete.gated.title", "identity.recoverComplete.gated.detail"],
      },
    };
    const selected = copy[kind];
    if (!selected) return [t("identity.unavailable.title"), t("identity.unavailable.detail")];
    const messageIds = available ? selected.ready : selected.gated;
    return messageIds.map((messageId) => t(messageId));
  }

  // Server-generated redirect codes are mapped to safe, accessible messages.
  // Never interpolate query text as HTML or read credentials in JavaScript.
  const IDENTITY_NOTICES = Object.freeze({
    login: {
      cadastro: {
        "verifique-email": ["success", "Cadastro recebido. Verifique seu e-mail para confirmar a conta antes de entrar."],
        confirmado: ["success", "E-mail confirmado. Entre na sua Conta OrdaX para continuar."],
      },
      erro: {
        formulario: ["error", "Revise o e-mail e a senha informados."],
        credenciais: ["error", "Não foi possível entrar. Confira suas credenciais e tente novamente."],
        "confirmacao-invalida": ["error", "O link de confirmação expirou ou já foi usado. Entre normalmente se seu e-mail já estiver confirmado."],
        "confirmacao-indisponivel": ["error", "Não foi possível verificar o e-mail agora. Tente novamente mais tarde."],
        "verificacao-falhou": ["error", "A verificação de segurança não foi concluída. Refaça a verificação e tente entrar novamente."],
        "seguranca-indisponivel": ["error", "A verificação de segurança está temporariamente indisponível. Tente novamente mais tarde."],
        "validacao-conta-indisponivel": ["error", "A validação da conta está indisponível. Tente novamente mais tarde."],
        "conta-requer-reconciliacao": ["error", "Sua conta precisa de validação adicional antes do acesso público."],
      },
    },
    register: {
      erro: {
        formulario: ["error", "Revise os dados de cadastro."],
        "aceite-legal": ["error", "É necessário ler e aceitar os documentos vigentes."],
        senha: ["error", "Escolha uma senha com pelo menos 12 caracteres."],
        "senha-comprometida": ["error", "Essa senha foi encontrada em vazamentos. Escolha outra."],
        "seguranca-indisponivel": ["error", "A verificação de segurança está indisponível. Tente novamente mais tarde."],
        "verificacao-falhou": ["error", "A verificação de segurança não foi concluída. Refaça a verificação antes de criar sua conta."],
        "politica-legal-indisponivel": ["error", "A política de cadastro está indisponível. O cadastro não foi concluído."],
        cadastro: ["error", "Não foi possível concluir o cadastro. Revise os dados e tente novamente."],
      },
    },
    recover: { erro: {
      formulario: ["error", "Informe um e-mail válido."],
      "verificacao-falhou": ["error", "A verificação de segurança falhou. Tente novamente."],
      "seguranca-indisponivel": ["error", "A verificação de segurança está indisponível. Tente novamente mais tarde."],
    } },
  });

  function showIdentityNotice(kind, available) {
    const notice = document.querySelector("[data-identity-notice]");
    if (!notice) return;
    notice.hidden = true;
    notice.removeAttribute("role");
    notice.textContent = "";
    if (!available) return;
    const allowed = IDENTITY_NOTICES[kind];
    if (!allowed) return;
    const params = new URLSearchParams(window.location.search);
    for (const key of ["erro", "cadastro"]) {
      const code = params.get(key);
      if (code === null) continue;
      if (!Object.hasOwn(allowed[key] ?? {}, code)) continue;
      const message = allowed[key][code];
      notice.textContent = message[1];
      notice.dataset.kind = message[0];
      notice.setAttribute("role", message[0] === "error" ? "alert" : "status");
      notice.hidden = false;
      return;
    }
  }

  function validSessionReadiness(value) {
    return value
      && value.$schema === "prototype-ordax.public-identity-session/1"
      && value.provider === "supabase"
      && (
        (value.authenticated === false && value.status === "anonymous")
        || (value.authenticated === true && value.status === "authenticated"
          && typeof value.subject === "string" && value.subject.length > 0)
      );
  }

  // One verified session request per page. No parallel client-side auth state.
  let sessionPromise = null;
  let sessionRevision = 0;
  const sessionObservers = new Set();
  let sessionView = Object.freeze({ status: "checking", email: "" });

  function publishSessionView(status, email = "") {
    sessionView = Object.freeze({ status, email });
    for (const observer of sessionObservers) {
      // A presentation failure must not change the canonical identity result.
      try { observer(sessionView); } catch { console.error("public-account-view-failed"); }
    }
  }

  function sessionEmail(session) {
    if (typeof session.email !== "string" || session.email.length > 254
      || /[\u0000-\u001f\u007f]/.test(session.email)) return "";
    return session.email.trim();
  }

  function invalidateIdentitySession(status = "checking") {
    sessionRevision++;
    startRevision++;
    sessionPromise = null;
    publishSessionView(status);
  }

  function verifiedIdentitySession() {
    if (!sessionPromise) {
      const revision = sessionRevision;
      // The central JSON loader owns the deadline for session requests too.
      sessionPromise = loadJson("/auth/session").then(session => {
        if (!validSessionReadiness(session)) throw new Error("invalid-identity-session");
        if (revision === sessionRevision) {
          publishSessionView(session.authenticated ? "authenticated" : "anonymous",
            session.authenticated ? sessionEmail(session) : "");
        }
        return session;
      }).catch(error => {
        if (revision === sessionRevision) publishSessionView("unavailable");
        throw error;
      });
    }
    return sessionPromise;
  }

  // Only the verified same-origin session may expose profile commands.
  // The menu is a shared presentation of existing account routes and logout;
  // it never owns cookies, tokens, or another session state.
  let disposeProfileMenu = () => {};
  let authHeaderRevision = 0;
  function attachProfileMenu(trigger, { accountRoute = "/conta/", publicView = null } = {}) {
    if (typeof document.createElement !== "function"
      || typeof trigger?.addEventListener !== "function"
      || !trigger.parentElement) return () => {};

    const menu = document.createElement("div");
    menu.id = "ordax-profile-menu";
    menu.className = "ordax-profile-menu";
    menu.setAttribute("role", "group");
    menu.setAttribute("aria-label", i18n.fromSource("Opções da conta"));
    menu.hidden = true;
    // Only registered portal routes are accepted; consumers cannot inject URLs.
    const route = "/conta/";
    const authenticated = !publicView || publicView.status === "authenticated";
    let identity = null;
    if (publicView) {
      identity = document.createElement("p");
      identity.className = "ordax-profile-identity";
      identity.textContent = publicView.email || t(`account.session.${publicView.status === "authenticated" ? "active" : publicView.status === "anonymous" ? "anonymous" : publicView.status === "unavailable" ? "unavailable" : "checking"}.title`);
      menu.appendChild(identity);
    }
    const destinations = authenticated ? [
      [route, "Visão geral"],
      ...(publicView ? [[route + "#dados-pessoais", "Dados pessoais"]] : []),
      [route + "#seguranca", "Segurança"],
      [route + "#dispositivos", "Dispositivos"],
      [route + "#preferencias", "Preferências"],
    ] : [["/login/", "Entrar"], ["/cadastro/", "Criar conta"]];
    for (const [href, title] of destinations) {
      const option = document.createElement("a");
      option.href = href;
      option.textContent = i18n.fromSource(title);
      menu.appendChild(option);
    }
    const form = document.createElement("form");
    form.action = "/auth/logout";
    form.method = "post";
    const signOut = document.createElement("button");
    signOut.type = "submit";
    signOut.className = "ordax-profile-signout";
    signOut.textContent = i18n.fromSource("Sair da conta");
    form.appendChild(signOut);
    if (authenticated) menu.appendChild(form);
    let retry = null;
    const onRetry = () => { void refreshPublicSession(); };
    if (publicView?.status === "unavailable") {
      retry = document.createElement("button");
      retry.type = "button";
      retry.textContent = i18n.fromSource("Tentar novamente");
      retry.addEventListener("click", onRetry);
      menu.appendChild(retry);
    }
    trigger.parentElement.appendChild(menu);
    trigger.setAttribute("role", "button");
    trigger.setAttribute("aria-controls", menu.id);
    trigger.setAttribute("aria-expanded", "false");
    const close = () => {
      menu.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    };
    const onSubmit = () => {
      // Keep the native form connected until the browser submits its POST.
      // The server alone clears/revokes cookies and confirms the outcome.
      close();
      if (identity) identity.textContent = "";
      invalidateIdentitySession("leaving");
    };
    form.addEventListener("submit", onSubmit);
    const open = () => {
      menu.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
    };
    const onTriggerClick = event => {
      if (event.defaultPrevented || event.button > 0
        || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
      event.preventDefault();
      if (menu.hidden) open();
      else close();
    };
    const onTriggerKey = event => {
      if (event.key === " " || event.key === "Spacebar") {
        event.preventDefault();
        if (menu.hidden) open();
        else close();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        open();
        menu.querySelector("a,button")?.focus();
      }
    };
    const onOutsideClick = event => {
      if (!menu.hidden && !menu.contains(event.target) && !trigger.contains(event.target)) close();
    };
    const onGlobalKey = event => {
      if (event.key === "Escape" && !menu.hidden) {
        close();
        trigger.focus();
      }
    };
    const onFocusOutside = event => {
      if (!menu.hidden && !menu.contains(event.target) && !trigger.contains(event.target)) close();
    };
    const onOptionClick = event => {
      for (let target = event.target; target && target !== menu; target = target.parentElement) {
        if (target.tagName?.toLowerCase() === "a") {
          close();
          break;
        }
      }
    };
    menu.addEventListener("click", onOptionClick);
    trigger.addEventListener("click", onTriggerClick);
    trigger.addEventListener("keydown", onTriggerKey);
    document.addEventListener("click", onOutsideClick);
    document.addEventListener("keydown", onGlobalKey);
    document.addEventListener("focusin", onFocusOutside);
    return () => {
      close();
      trigger.removeEventListener("click", onTriggerClick);
      trigger.removeEventListener("keydown", onTriggerKey);
      document.removeEventListener("click", onOutsideClick);
      document.removeEventListener("keydown", onGlobalKey);
      document.removeEventListener("focusin", onFocusOutside);
      menu.removeEventListener("click", onOptionClick);
      form.removeEventListener("submit", onSubmit);
      retry?.removeEventListener("click", onRetry);
      trigger.removeAttribute("role");
      trigger.removeAttribute("aria-controls");
      trigger.removeAttribute("aria-expanded");
      menu.remove();
    };
  }

  async function readPublicSession() {
    if (sessionView.status === "leaving") return sessionView;
    try { await verifiedIdentitySession(); } catch { /* Unavailable is a presentation state. */ }
    return sessionView;
  }

  function refreshPublicSession() {
    if (sessionView.status === "leaving") return Promise.resolve(sessionView);
    invalidateIdentitySession();
    void start();
    return readPublicSession();
  }

  // Versioned presentation port of the existing portal client. No tokens,
  // subject IDs, additional cache or provider SDK reach consumers.
  window.OrdaXPublicAccount = Object.freeze({
    schema: "prototype-ordax.public-account-client/1",
    getSnapshot: () => sessionView,
    readSession: readPublicSession,
    refreshSession: refreshPublicSession,
    // Read-only account data uses the same bounded same-origin transport.
    // Authorization remains entirely server-side; no client-side quota claim.
    async readMcpUsage(signal) {
      const owner = sessionView;
      if (owner.status !== "authenticated") {
        throw new Error("public-account-session-required");
      }
      const payload = await loadJson("/account/usage/mcp", signal);
      // A successful HTTP response from a previous session is not current
      // account data, even when the new session has the same display email.
      if (owner !== sessionView || sessionView.status !== "authenticated") {
        throw new Error("public-account-session-changed");
      }
      return payload;
    },
    async readMcpAuthority(deviceId, signal) {
      const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const owner = sessionView;
      if (owner.status !== "authenticated") throw new Error("public-account-session-required");
      if (!uuid.test(deviceId)) throw new Error("mcp-owner-device-invalid");
      const value = await loadJson("/account/mcp/authority?device_id=" + deviceId, signal,
        { maxBytes: 64 * 1024 });
      const clients = value?.clients;
      const grants = value?.grant_groups;
      if (!value || value.ok !== true || value.schema !== "ordax.owner-mcp-authority-view/1"
          || value.device_id !== deviceId || !Array.isArray(clients) || clients.length > 100
          || !Array.isArray(grants) || grants.length > 256
          || new Set(clients.map(c => c?.client_id)).size !== clients.length
          || new Set(grants.map(g => g?.grant_group_id)).size !== grants.length
          || !clients.every(c => c && uuid.test(c.client_id)
            && typeof c.client_name === "string" && c.client_name.length <= 120)
          || !grants.every(g => g && uuid.test(g.grant_group_id) && uuid.test(g.client_id)
            && /^[a-z][a-z0-9._-]{1,79}$/.test(g.profile_key)
            && typeof g.client_consent_active === "boolean"
            && (g.valid_until === null || (typeof g.valid_until === "string"
              && Number.isFinite(Date.parse(g.valid_until)))))) {
        throw new Error("mcp-owner-authority-invalid");
      }
      if (owner !== sessionView || sessionView.status !== "authenticated")
        throw new Error("public-account-session-changed");
      return value;
    },
    async revokeMcpGrant(input, signal) {
      const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const owner = sessionView;
      if (owner.status !== "authenticated") throw new Error("public-account-session-required");
      if (!input || Object.keys(input).sort().join(",") !== "client_id,confirm,device_id,grant_group_id"
          || !uuid.test(input.device_id) || !uuid.test(input.client_id)
          || !uuid.test(input.grant_group_id) || input.confirm !== "revogar")
        throw new Error("mcp-owner-revoke-invalid");
      // Same-origin HttpOnly cookies, browser Origin and Fetch Metadata only;
      // the Product bearer remains inside the authenticated Account gateway.
      const value = await loadJson("/account/mcp/revoke", signal,
        { maxBytes: 4096, method: "POST", jsonBody: input });
      if (!value || value.ok !== true || value.schema !== "ordax.owner-mcp-revocation/1"
          || value.revoked !== true || value.device_id !== input.device_id
          || value.client_id !== input.client_id || value.grant_group_id !== input.grant_group_id)
        throw new Error("mcp-owner-revoke-unconfirmed");
      if (owner !== sessionView || sessionView.status !== "authenticated")
        throw new Error("public-account-session-changed");
      return value;
    },
    async readMcpCentralTargets(clientId, signal) {
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const owner=sessionView;
      if(owner.status!=="authenticated")throw Error("public-account-session-required");
      if(!uuid.test(clientId))throw Error("mcp-owner-client-invalid");
      const value=await loadJson("/account/mcp/central-targets?client_id="+clientId,signal,
        {maxBytes:8192});
      if(!value||value.ok!==true||value.schema!=="ordax.owner-central-targets/1"
          ||value.client_id!==clientId||value.attested!==false
          ||value.dispatch_authorized!==false
          ||!Number.isSafeInteger(value.eligible_device_count)
          ||value.eligible_device_count<0||value.eligible_device_count>25
          ||!Array.isArray(value.targets)||value.targets.length!==value.eligible_device_count
          ||new Set(value.targets.map(t=>t?.device_id)).size!==value.targets.length
          ||!value.targets.every(t=>t&&uuid.test(t.device_id)
            &&typeof t.reported_online==="boolean"&&typeof t.runtime_ready==="boolean"))
        throw Error("mcp-owner-central-targets-invalid");
      if(owner!==sessionView||sessionView.status!=="authenticated")
        throw Error("public-account-session-changed");
      return value;
    },
    async readMcpCentralSelections(clientId, signal) {
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const owner=sessionView;
      if(owner.status!=="authenticated")throw Error("public-account-session-required");
      if(!uuid.test(clientId))throw Error("mcp-owner-client-invalid");
      const value=await loadJson("/account/mcp/central-selections?client_id="+clientId,
        signal,{maxBytes:8192});
      if(!value||value.ok!==true||value.schema!=="ordax.owner-central-selections/1"
          ||value.client_id!==clientId||value.attested!==false
          ||value.dispatch_authorized!==false
          ||!Number.isSafeInteger(value.count)||value.count<0||value.count>25
          ||!Array.isArray(value.pending_selections)
          ||value.pending_selections.length!==value.count
          ||new Set(value.pending_selections.map(t=>t?.challenge_id)).size!==value.count
          ||!value.pending_selections.every(t=>t&&uuid.test(t.challenge_id)
            &&typeof t.created_at==="string"&&Number.isFinite(Date.parse(t.created_at))
            &&typeof t.expires_at==="string"&&Number.isFinite(Date.parse(t.expires_at))))
        throw Error("mcp-owner-central-selections-invalid");
      if(owner!==sessionView||sessionView.status!=="authenticated")
        throw Error("public-account-session-changed");
      return value;
    },
    async selectMcpCentralDevice(input, signal) {
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const owner=sessionView;
      if(owner.status!=="authenticated")throw Error("public-account-session-required");
      if(!input||Object.keys(input).sort().join(",")
          !=="challenge_id,client_id,confirm,device_id"
          ||!uuid.test(input.client_id)||!uuid.test(input.challenge_id)
          ||!uuid.test(input.device_id)||input.confirm!=="selecionar")
        throw Error("mcp-owner-central-selection-invalid");
      const value=await loadJson("/account/mcp/central-selections",signal,
        {maxBytes:4096,method:"POST",jsonBody:input});
      if(!value||value.ok!==true
          ||value.schema!=="ordax.owner-central-device-selection/1"
          ||value.status!=="pending"||value.client_id!==input.client_id
          ||value.device_id!==input.device_id||value.challenge_id!==input.challenge_id
          ||value.attested!==false||value.dispatch_authorized!==false
          ||typeof value.expires_at!=="string"||!Number.isFinite(Date.parse(value.expires_at)))
        throw Error("mcp-owner-central-selection-unconfirmed");
      if(owner!==sessionView||sessionView.status!=="authenticated")
        throw Error("public-account-session-changed");
      return value;
    },
    async readMcpProjectOnboarding(deviceId, signal) {
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const kinds=new Set(["general","development","creative","legal","business","research"]);
      const states=new Set(["needs_github_installation","needs_repository_selection",
        "needs_device_binding","ready_without_grants"]);
      const rootStates=new Set(["needs_space","needs_project"]);
      const repository=/^[A-Za-z0-9-]+\/[A-Za-z0-9._-]+$/;
      const owner=sessionView;
      if(owner.status!=="authenticated")throw Error("public-account-session-required");
      if(!uuid.test(deviceId))throw Error("mcp-owner-device-invalid");
      const value=await loadJson("/account/mcp/project-onboarding?device_id="+deviceId,signal,
        {maxBytes:128*1024});
      const spaces=value?.spaces,projects=value?.projects;
      if(!value||value.ok!==true||value.schema!=="ordax.owner-project-onboarding-view/1"
          ||value.device_id!==deviceId||!Array.isArray(spaces)||spaces.length>64
          ||!Array.isArray(projects)||projects.length>512
          ||new Set(spaces.map(s=>s?.space_id)).size!==spaces.length
          ||new Set(projects.map(p=>p?.project_id)).size!==projects.length
          ||!spaces.every(s=>s&&uuid.test(s.space_id)&&typeof s.name==="string"
            &&s.name.length>0&&s.name.length<=120&&typeof s.kind==="string"
            &&s.kind.length>0&&s.kind.length<=80&&s.state==="active")
          ||!projects.every(p=>p&&uuid.test(p.project_id)&&uuid.test(p.space_id)
            &&spaces.some(s=>s.space_id===p.space_id)&&typeof p.name==="string"
            &&p.name.length>0&&p.name.length<=120&&kinds.has(p.kind)&&p.state==="active"
            &&Number.isSafeInteger(p.github_connection_count)&&p.github_connection_count>=0
            &&typeof p.space_device_execute==="boolean"&&typeof p.project_device_bound==="boolean"
            &&states.has(p.next_state)
            &&(p.repository_full_name===null||(typeof p.repository_full_name==="string"
              &&p.repository_full_name.length<=220&&repository.test(p.repository_full_name)))
            &&((p.github_connection_count===1)===(p.repository_full_name!==null)))
          ||!(value.next_state===null||rootStates.has(value.next_state))
          ||(value.next_state==="needs_space"&&spaces.length!==0)
          ||(value.next_state==="needs_project"&&(spaces.length===0||projects.length!==0))
          ||(value.next_state===null&&(spaces.length===0||projects.length===0)))
        throw Error("mcp-owner-project-onboarding-invalid");
      if(owner!==sessionView||sessionView.status!=="authenticated")
        throw Error("public-account-session-changed");
      return value;
    },
    async createMcpProject(input, signal) {
      const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
      const kinds=new Set(["general","development","creative","legal","business","research"]);
      const owner=sessionView;
      if(owner.status!=="authenticated")throw Error("public-account-session-required");
      if(!input||Object.keys(input).sort().join(",")!=="confirm,kind,name,space_id"
          ||!uuid.test(input.space_id)||!kinds.has(input.kind)
          ||typeof input.name!=="string"||input.name.trim().length<1
          ||input.name.trim().length>120||/[\u0000-\u001f\u007f]/.test(input.name)
          ||input.confirm!=="create_project")
        throw Error("mcp-owner-project-create-invalid");
      const request={space_id:input.space_id,name:input.name.trim(),
        kind:input.kind,confirm:"create_project"};
      const value=await loadJson("/account/mcp/project-onboarding/projects",signal,
        {maxBytes:4096,method:"POST",jsonBody:request});
      if(!value||value.ok!==true||value.schema!=="ordax.owner-project-created/1"
          ||!uuid.test(value.project_id)||value.space_id!==request.space_id
          ||value.state!=="active"||value.next_state!=="needs_github_installation")
        throw Error("mcp-owner-project-create-unconfirmed");
      if(owner!==sessionView||sessionView.status!=="authenticated")
        throw Error("public-account-session-changed");
      return value;
    },
    // Reuse Account's authenticated same-origin transport: no Product tokens in JS.
    async readMcpDevices(signal) {
      const owner = sessionView;
      if (owner.status !== "authenticated") throw new Error("public-account-session-required");
      const value = await loadJson("/account/mcp/devices", signal, { maxBytes: 64 * 1024 });
      const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      if (!value || value.ok !== true || value.schema !== "ordax.owner-mcp-devices/1"
          || !Array.isArray(value.devices) || value.devices.length > 200
          || value.count !== value.devices.length
          || new Set(value.devices.map(item => item?.device_id)).size !== value.devices.length
          || !value.devices.every(item => item && uuid.test(item.device_id)
            && typeof item.name === "string" && item.name.length > 0 && item.name.length <= 120
            && typeof item.kind === "string" && item.kind.length <= 80
            && typeof item.channel === "string" && item.channel.length <= 80
            && typeof item.state === "string" && item.state.length <= 80
            && typeof item.online === "boolean" && typeof item.runtime_ready === "boolean"
            && (item.last_seen_at === null || (typeof item.last_seen_at === "string"
              && Number.isFinite(Date.parse(item.last_seen_at)))))) {
        throw new Error("public-account-mcp-devices-invalid");
      }
      if (owner !== sessionView || sessionView.status !== "authenticated") {
        throw new Error("public-account-session-changed");
      }
      return value;
    },
    subscribe(observer) {
      if (typeof observer !== "function") throw new TypeError("account-observer-required");
      sessionObservers.add(observer);
      try { observer(sessionView); } catch { console.error("public-account-view-failed"); }
      return () => sessionObservers.delete(observer);
    },
    bindProfileMenu(trigger, options) {
      return attachProfileMenu(trigger, { accountRoute: options?.accountRoute, publicView: sessionView });
    },
  });

  async function renderAuthHeader() {
    // Concurrent locale/session checks cannot attach duplicate menus.
    const headerRevision = ++authHeaderRevision;
    // Revalidation or back-navigation destroys stale authenticated controls.
    disposeProfileMenu();
    disposeProfileMenu = () => {};
    const header = document.querySelector(".site-header");
    const login = header?.querySelector('[data-auth-nav="login"]');
    const register = header?.querySelector('[data-auth-nav="register"]');
    if (!login && !register) return;
    const label = link => link?.querySelector("[data-auth-nav-label]");
    const revision = sessionRevision;
    // Fail closed and restore anonymous navigation before revalidation.
    if (login) {
      login.href = "/login/";
      login.removeAttribute("aria-current");
      const caption = label(login);
      if (caption) caption.textContent = i18n.fromSource("Entrar");
    }
    if (register) {
      register.href = "/cadastro/";
      register.hidden = false;
      register.removeAttribute("aria-current");
      const caption = label(register);
      if (caption) caption.textContent = i18n.fromSource("Criar conta");
    }
    try {
      const session = await verifiedIdentitySession();
      if (headerRevision !== authHeaderRevision
        || revision !== sessionRevision || !session.authenticated) return;
      const accountLink = login || register;
      accountLink.href = "/conta/";
      const caption = label(accountLink);
      if (caption) caption.textContent = t("account.navigation.account");
      if (document.body?.dataset?.page === "conta") accountLink.setAttribute("aria-current", "page");
      if (login && register) register.hidden = true;
      disposeProfileMenu = attachProfileMenu(accountLink);
    } catch {
      // No connection or no valid session: only public links remain.
    }
  }

  function productWebEntry(config) {
    const product = config?.product?.web;
    const path = product?.entry_url;
    // Navigation only; the deployed product host must independently authorize every request.
    if (product?.enabled !== true || typeof path !== "string"
      || !/^\/[A-Za-z0-9/_-]+\/$/.test(path)
      || /\/\//.test(path)
      || /^\/(?:auth|account|sync|config|api|conta|login|cadastro|web)(?:\/|$)/.test(path)) return null;
    return path;
  }

  let webRenderRevision = 0;
  async function renderWebEntry(config) {
    const state = document.querySelector("[data-web-state]");
    const launch = document.querySelector("[data-web-launch]");
    const login = document.querySelector("[data-web-login]");
    const retry = document.querySelector("[data-web-retry]");
    if (!state || !launch || !login || !retry) return;
    const generation = ++webRenderRevision;
    const revision = sessionRevision;
    const pageRevision = startRevision;
    launch.hidden = login.hidden = retry.hidden = true;
    launch.removeAttribute("href");
    state.dataset.status = "checking";
    state.setAttribute("aria-busy", "true");
    setStatus("[data-web-state]", t("web.entry.checking.title"), t("web.entry.checking.detail"));
    // Product availability is defined by the signed Site runtime config,
    // never inferred from a session or from a hard-coded external host.
    // When disabled/unconfigured, avoid inviting the visitor to sign in.
    const path = productWebEntry(config);
    if (!path) {
      state.dataset.status = "unavailable";
      state.removeAttribute("aria-busy");
      setStatus("[data-web-state]", t("web.entry.pending.title"), t("web.entry.pending.detail"));
      return;
    }
    try {
      const session = await verifiedIdentitySession();
      if (revision !== sessionRevision || generation !== webRenderRevision || pageRevision !== startRevision) return;
      if (!session.authenticated) {
        login.hidden = false;
        state.dataset.status = "anonymous";
        setStatus("[data-web-state]", t("web.entry.anonymous.title"), t("web.entry.anonymous.detail"));
      } else {
        launch.href = path;
        launch.hidden = false;
        state.dataset.status = "ready";
        setStatus("[data-web-state]", t("web.entry.ready.title"), t("web.entry.ready.detail"));
      }
    } catch {
      if (revision !== sessionRevision || generation !== webRenderRevision || pageRevision !== startRevision) return;
      retry.hidden = false;
      state.dataset.status = "error";
      setStatus("[data-web-state]", t("web.entry.error.title"), t("web.entry.error.detail"));
    } finally {
      if (revision === sessionRevision && generation === webRenderRevision && pageRevision === startRevision) state.removeAttribute("aria-busy");
    }
  }

  async function renderIdentity(config, generation) {
    const state = document.querySelector("[data-identity-state]");
    const form = document.querySelector("[data-identity-form]");
    if (!state || !form) return;
    const sessionAtStart = sessionRevision;
    const isCurrent = () => generation === startRevision && sessionAtStart === sessionRevision;

    const kind = form.dataset.identityForm;
    // Explicit, local-only presentation mode. Render the SAME native form,
    // inert and disabled, without querying Identity or loading Turnstile.
    // This does not enable the public sign-in flow or simulate a session.
    const layoutPreview = ["login", "register", "recover", "recover-complete"].includes(kind)
      && isIdentityLayoutPreview();
    if (layoutPreview) {
      form.removeAttribute("action");
      form.inert = true;
      for (const control of form.querySelectorAll("input, button")) control.disabled = true;
      form.onsubmit = (event) => event.preventDefault();
      form.hidden = false;
      if (kind === "register") {
        // Show existing legal controls as an inert illustration, never a
        // verified policy or recorded acceptance. Live registration below
        // still requires its server-owned, hash-verified legal documents.
        const legal = form.querySelector("[data-registration-legal]");
        if (legal) legal.hidden = false;
      }
      state.dataset.status = "preview";
      state.removeAttribute("aria-busy");
      const title = state.querySelector("strong");
      const detail = state.querySelector("p");
      if (title) title.textContent = t("identity.layoutPreview.title");
      if (detail) detail.textContent = t("identity.layoutPreview.detail");
      document.body.dataset.identityReady = "false";
      document.body.dataset.identityPreview = "layout";
      return;
    }
    const routes = {
      login: ["/auth/login", config?.identity?.login_url],
      register: ["/auth/register", config?.identity?.register_url],
      recover: ["/auth/recover", config?.identity?.recovery_url],
      "recover-complete": ["/auth/recover/complete", config?.identity?.recovery_complete_url],
    };
    const route = routes[kind];
    const expectedTarget = route?.[0] ?? null;
    const target = route?.[1] ?? null;
    const legalReady = config?.legal?.account_activation_ready === true;
    // Login and signup can ship without activating unrelated Cloud features.
    // This static flag only makes the form eligible for *live server checks*;
    // the session and active legal policy are authoritative.
    const authOnly = config?.legal?.auth_only_source_enabled === true
      && (kind === "login" || kind === "register");
    let available = (legalReady || authOnly)
      && target === expectedTarget && sameOriginPath(target);
    if (available) {
      try {
        // The server is authoritative: a static configuration alone cannot
        // enable forms when the public identity gateway is unavailable.
        available = !!(await verifiedIdentitySession());
        if (!isCurrent()) return;
      } catch {
        if (!isCurrent()) return;
        available = false;
      }
    }
    if (available && kind === "register") {
      try {
        const policy = await loadJson("/auth/registration-policy");
        if (!isCurrent()) return;
        const verified = await verifyPublishedRegistrationDocuments(policy);
        if (!isCurrent()) return;
        available = verified && renderRegistrationPolicy(form, policy);
        if (!available) renderRegistrationPolicy(form, null);
      } catch {
        if (!isCurrent()) return;
        available = false;
        renderRegistrationPolicy(form, null);
      }
    }
    if (
      available
      && TURNSTILE_PROTECTED_KINDS.has(kind)
      && !validTurnstileSitekey(config?.identity?.turnstile_sitekey)
    ) {
      available = false;
    }

    if (!isCurrent()) return;
    const controls = form.querySelectorAll("input, button");
    if (available) {
      form.action = target;
      form.hidden = false;
      for (const control of controls) control.disabled = false;
      if (TURNSTILE_PROTECTED_KINDS.has(kind)) {
        available = await armTurnstile(form, config.identity.turnstile_sitekey, isCurrent);
        if (!isCurrent()) return;
      }
    }
    if (!available) {
      form.removeAttribute("action");
      form.hidden = true;
      for (const control of controls) control.disabled = true;
    }

    const [title, detail] = identityCopy(kind, available);
    const strong = state.querySelector("strong");
    const paragraph = state.querySelector("p");
    if (strong) strong.textContent = title;
    if (paragraph) paragraph.textContent = detail;
    state.dataset.status = available ? "ready" : "unavailable";
    state.removeAttribute("aria-busy");
    document.body.dataset.identityReady = available ? "true" : "false";
    showIdentityNotice(kind, available);
  }

  function validSha256(value) {
    return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
  }

  function validIntegrityArtifact(value) {
    return (
      value &&
      sameOriginPath(value.href) &&
      validSha256(value.sha256) &&
      Number.isInteger(value.size) &&
      value.size > 0
    );
  }

  function releaseTargetNode(target) {
    if (
      !target ||
      !sameOriginPath(target.href) ||
      typeof target.label !== "string" ||
      !validSha256(target.sha256) ||
      !Number.isInteger(target.size) ||
      target.size <= 0
    ) {
      return null;
    }

    const row = document.createElement("div");
    row.className = "release-target";

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const hash = document.createElement("code");
    title.textContent = target.label;
    hash.textContent = `SHA-256 ${target.sha256}`;
    copy.append(title, document.createElement("br"), hash);

    const link = document.createElement("a");
    link.className = "button button-primary";
    link.href = target.href;
    link.textContent = t("download.action");

    row.append(copy, link);
    return row;
  }

  function complianceArtifactNode(label, artifact, actionLabel = null) {
    if (!validIntegrityArtifact(artifact)) return null;

    const row = document.createElement("div");
    row.className = "compliance-artifact";

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const hash = document.createElement("code");
    const size = document.createElement("span");
    title.textContent = label;
    hash.textContent = `SHA-256 ${artifact.sha256}`;
    size.textContent = ` · ${artifact.size} bytes`;
    copy.append(title, document.createElement("br"), hash, size);

    const link = document.createElement("a");
    link.className = "button button-quiet";
    link.href = artifact.href;
    link.textContent = actionLabel ?? t("compliance.open");

    row.append(copy, link);
    return row;
  }

  function releaseComplianceNode(compliance) {
    if (!compliance || typeof compliance !== "object") return null;

    const entries = [
      ["SBOM", compliance.sbom, "SBOM"],
      [t("compliance.thirdParty.label"), compliance.third_party_notices, t("compliance.thirdParty.action")],
      [t("compliance.source.label"), compliance.source_bundle, t("compliance.source.action")],
    ];

    const section = document.createElement("section");
    section.className = "release-compliance";

    const heading = document.createElement("div");
    heading.className = "release-compliance-heading";
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = t("compliance.heading");
    const intro = document.createElement("p");
    intro.textContent = t("compliance.intro");
    heading.append(eyebrow, intro);
    section.append(heading);

    let count = 0;
    for (const [label, artifact, actionLabel] of entries) {
      const row = complianceArtifactNode(label, artifact, actionLabel);
      if (!row) continue;
      section.append(row);
      count += 1;
    }
    return count === entries.length ? section : null;
  }

  function validCatalog(catalog) {
    // Reject the *whole* response before producing any download link.
    // A JSON status flag is not permission to publish: the build still emits
    // an empty catalog until publisher attestation is integrated separately.
    if (!catalog || catalog.$schema !== CATALOG_SCHEMA ||
        !Array.isArray(catalog.releases) ||
        (catalog.status !== "empty" && catalog.status !== "ready")) return false;
    if (catalog.status === "empty") return catalog.releases.length === 0;
    if (catalog.releases.length === 0) return false;

    const releaseIds = new Set();
    for (const release of catalog.releases) {
      if (!release || typeof release !== "object" ||
          typeof release.release_id !== "string" ||
          !/^[0-9a-f]{40}$/.test(release.release_id) ||
          release.source_commit !== release.release_id ||
          releaseIds.has(release.release_id) ||
          !["version", "channel", "published_at"].every(
            key => typeof release[key] === "string" && release[key].trim()
          ) || !Array.isArray(release.targets) || release.targets.length === 0) {
        return false;
      }
      releaseIds.add(release.release_id);
      const ids = new Set();
      for (const target of release.targets) {
        if (!target || typeof target.id !== "string" || !target.id.trim() ||
            ids.has(target.id) || typeof target.label !== "string" ||
            !target.label.trim() || !validIntegrityArtifact(target)) return false;
        ids.add(target.id);
      }
      const compliance = release.compliance;
      if (!compliance || !["sbom", "third_party_notices", "source_bundle"].every(
        key => validIntegrityArtifact(compliance[key])
      )) return false;
    }
    return true;
  }

  function renderCatalog(catalog) {
    if (!validCatalog(catalog)) {
      throw new Error("invalid-public-release-catalog");
    }

    const list = document.querySelector("[data-release-list]");
    if (!list) return 0;
    list.replaceChildren();

    let rendered = 0;
    for (const release of catalog.releases) {
      if (!release || typeof release.version !== "string" || !Array.isArray(release.targets)) continue;

      const compliance = releaseComplianceNode(release.compliance);
      if (!compliance) continue;

      const card = document.createElement("article");
      card.className = "release-card";

      const header = document.createElement("div");
      header.className = "release-card-header";
      const title = document.createElement("h2");
      title.textContent = release.version;
      const meta = document.createElement("p");
      const channel = typeof release.channel === "string" ? release.channel : "public";
      const date = typeof release.published_at === "string" ? ` · ${release.published_at}` : "";
      meta.textContent = `${channel}${date}`;
      header.append(title, meta);
      card.append(header);

      let targetCount = 0;
      for (const target of release.targets) {
        const row = releaseTargetNode(target);
        if (!row) continue;
        card.append(row);
        targetCount += 1;
      }

      if (targetCount > 0) {
        card.append(compliance);
        list.append(card);
        rendered += 1;
      }
    }
    return rendered;
  }

  function renderComplianceCatalog(catalog) {
    if (!validCatalog(catalog)) {
      throw new Error("invalid-public-release-catalog");
    }

    const list = document.querySelector("[data-compliance-list]");
    if (!list) return 0;
    list.replaceChildren();

    let rendered = 0;
    for (const release of catalog.releases) {
      if (!release || typeof release.version !== "string") continue;
      const compliance = releaseComplianceNode(release.compliance);
      if (!compliance) continue;

      const card = document.createElement("article");
      card.className = "release-card";

      const header = document.createElement("div");
      header.className = "release-card-header";
      const title = document.createElement("h2");
      title.textContent = release.version;
      const meta = document.createElement("p");
      const source = typeof release.source_commit === "string"
        ? `commit ${release.source_commit.slice(0, 12)}`
        : t("release.public");
      meta.textContent = source;
      header.append(title, meta);
      card.append(header, compliance);
      list.append(card);
      rendered += 1;
    }
    return rendered;
  }

  function setStatus(selector, title, detail) {
    const status = document.querySelector(selector);
    if (!status) return;
    const strong = status.querySelector("strong");
    const paragraph = status.querySelector("p");
    if (strong) strong.textContent = title;
    if (paragraph) paragraph.textContent = detail;
  }

  async function loadPublicCatalog(config) {
    // The Site's independent build publishes exactly one catalog file and its
    // byte digest in the existing immutable bundle inventory. A well-formed
    // same-origin API response alone is not publication authorization.
    const catalogPath = config?.downloads?.catalog_url;
    if (catalogPath !== "/releases/catalog.json") {
      throw new Error("catalog-not-configured");
    }
    const [manifest, response] = await Promise.all([
      loadJson("/public-site-manifest.json"),
      fetch(catalogPath, {
        method: "GET", credentials: "same-origin", cache: "no-store",
        redirect: "error", headers: { Accept: "application/json" },
      }),
    ]);
    if (!response.ok || !manifest ||
        manifest.$schema !== "prototype-ordax.independent-public-site-bundle/1" ||
        manifest.artifact_class !== "public-site" ||
        !/^[0-9a-f]{40}$/.test(manifest.source_commit) ||
        !Array.isArray(manifest.files)) {
      throw new Error("catalog-bundle-not-verified");
    }
    const records = manifest.files.filter(row => row?.path === "releases/catalog.json");
    if (records.length !== 1) throw new Error("catalog-inventory-invalid");
    const record = records[0];
    if (!validSha256(record.sha256) ||
        !Number.isSafeInteger(record.size) || record.size < 0 || record.size > 262144) {
      throw new Error("catalog-inventory-invalid");
    }
    // Reuse the same bounded JSON reader; the catalog additionally needs an
    // exact-byte match against the candidate's existing immutable inventory.
    if (!window.crypto?.subtle || response.redirected ||
        response.url !== new URL(catalogPath, window.location.origin).href) {
      throw new Error("catalog-bundle-mismatch");
    }
    const bytes = await readJsonBytes(response, record.size);
    if (bytes.length !== record.size) throw new Error("catalog-bundle-mismatch");
    const actualHash = await crypto.subtle.digest("SHA-256", bytes);
    const actualSha256 = [...new Uint8Array(actualHash)]
      .map(byte => byte.toString(16).padStart(2, "0")).join("");
    if (actualSha256 !== record.sha256) throw new Error("catalog-bundle-mismatch");

    const catalog = parseJsonBytes(bytes);
    if (!validCatalog(catalog) || manifest.catalog_status !== catalog.status) {
      throw new Error("catalog-publication-state-mismatch");
    }
    // No authorized publisher integration exists in this version.
    // Never let a self-authored same-origin manifest invent authority.
    // This block must be redesigned only alongside a verified publisher gate.
    if (catalog.status !== "empty" || manifest.publications_sha256 !== null) {
      throw new Error("catalog-publisher-not-attested");
    }
    return catalog;
  }

  async function initDownload(config) {
    try {
      const catalog = await loadPublicCatalog(config);
      const count = renderCatalog(catalog);
      if (count === 0) {
        setStatus(
          "[data-download-status]",
          t("download.empty.title"),
          t("download.empty.detail")
        );
        return;
      }
      setStatus(
        "[data-download-status]",
        t("download.ready.title"),
        t("download.ready.detail")
      );
    } catch {
      setStatus(
        "[data-download-status]",
        t("download.error.title"),
        t("download.error.detail")
      );
    }
  }

  async function initCompliance(config) {
    try {
      const catalog = await loadPublicCatalog(config);
      const count = renderComplianceCatalog(catalog);
      if (count === 0) {
        setStatus(
          "[data-compliance-status]",
          t("compliance.empty.title"),
          t("compliance.empty.detail")
        );
        return;
      }
      setStatus(
        "[data-compliance-status]",
        t("compliance.ready.title"),
        t("compliance.ready.detail")
      );
    } catch {
      setStatus(
        "[data-compliance-status]",
        t("compliance.error.title"),
        t("compliance.error.detail")
      );
    }
  }

  let startRevision = 0;
  async function start() {
    const generation = ++startRevision;
    // Hosted Identity redirects can leave bearer-like key/value fragments on
    // any presentation form route. The Site never consumes these credentials:
    // discard them synchronously before config, Turnstile or other requests.
    // Keep ordinary #conteudo anchors functional for keyboard navigation.
    if (IDENTITY_PREVIEW_PATHS.has(window.location.pathname)
        && window.location.hash.includes("=")) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
    // A second locale/session check revokes any previous form or challenge
    // synchronously, before waiting for the config or the Identity gateway.
    const identityForm = document.querySelector("[data-identity-form]");
    if (identityForm && !isIdentityLayoutPreview()) {
      removeTurnstile();
      identityForm.removeAttribute("action");
      identityForm.hidden = true;
      for (const control of identityForm.querySelectorAll("input, button")) {
        control.disabled = true;
      }
      document.body.dataset.identityReady = "false";
      const state = document.querySelector("[data-identity-state]");
      if (state) {
        state.dataset.status = "checking";
        state.setAttribute("aria-busy", "true");
      }
    }
    const webLaunch = document.querySelector("[data-web-launch]");
    if (webLaunch) {
      webLaunch.hidden = true;
      webLaunch.removeAttribute("href");
    }
    // Navigation does not block the page; the account portal shares its read.
    void renderAuthHeader();
    let config = null;
    try {
      config = await loadConfig();
    } catch {
      config = null;
    }
    if (generation !== startRevision) return;

    const page = document.body?.dataset?.page;
    if (page === "conta") {
      await readPublicSession();
    } else if (page === "web") {
      await renderWebEntry(config);
    } else if (page === "download") {
      await initDownload(config);
    } else if (page === "licencas") {
      await initCompliance(config);
    } else if (
      page === "login"
      || page === "cadastro"
      || page === "recuperar"
      || page === "recuperar-nova-senha"
    ) {
      await renderIdentity(config, generation);
    }
  }

  if (isIdentityLayoutPreview()) {
    // Preserve the explicit read-only context for ordinary identity links,
    // including new-tab clicks. Let the browser perform native navigation.
    const preserveLayoutPreview = (event) => {
      if (event.defaultPrevented || event.button > 1) return;
      const link = event.target?.closest?.("a[href]");
      if (!link) return;
      let target;
      try { target = new URL(link.href, window.location.href); }
      catch { return; }
      if (target.origin !== window.location.origin
          || !IDENTITY_PREVIEW_PATHS.has(target.pathname)) return;
      target.searchParams.set("preview", "layout");
      link.href = target.href;
    };
    document.addEventListener("click", preserveLayoutPreview, true);
    document.addEventListener("auxclick", preserveLayoutPreview, true);
  }

  document.addEventListener("ordax:localechange", () => {
    void start();
  });

  // Back navigation after logout must never show a cached authenticated view.
  window.addEventListener("pageshow", event => {
    if (!event.persisted) return;
    invalidateIdentitySession();
    void start();
    if (document.body?.dataset?.page === "conta") void readPublicSession();
  });

  window.addEventListener("pagehide", () => {
    invalidateIdentitySession();
    removeTurnstile();
    disposeProfileMenu();
    disposeProfileMenu = () => {};
  });

  // A logout in another tab must be discovered when the account becomes visible.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible"
      || !["conta", "web"].includes(document.body?.dataset?.page)) return;
    void refreshPublicSession();
  });

  void start();
})();
