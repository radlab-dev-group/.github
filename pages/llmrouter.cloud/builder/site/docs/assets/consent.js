/* ==========================================================================
   llm-router -- analytics consent gate.
   The Google Analytics payload lives in tools/ga_code.txt. The builder
   injects it into this file (the @@GA@@ token below) and writes the result to
   docs/assets/consent.js, which every page loads. Nothing is requested from
   Google until the visitor has chosen: accepted -> the payload is injected,
   declined -> nothing is ever loaded, postponed ("decide later") -> nothing is
   loaded and the panel stays quiet for LATER_QUIET_PERIOD. The decision is
   stored in localStorage and any element carrying a data-consent-open
   attribute reopens the panel.

   The payload is always preceded by a Google Consent Mode v2 default that
   denies every category. Accepting grants analytics_storage only, so an
   analytics consent never implies advertising storage.
   No dependencies, no build step; shared by the landing page and the docs.
   ========================================================================== */
(function () {
  "use strict";

  var doc = document;
  var GA_PAYLOAD = "\u003cscript async src=\"https://www.googletagmanager.com/gtag/js?id=G-9KM7GYM55M\"\u003e\u003c/script\u003e\n\u003cscript\u003ewindow.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-9KM7GYM55M');\u003c/script\u003e";
  var STORAGE_KEY = "llmrouter.analytics.consent.v1";
  /* "decide later" silences the panel for this long without granting anything */
  var LATER_QUIET_PERIOD = 30 * 24 * 60 * 60 * 1000;
  /* Google Consent Mode v2 categories, always denied unless granted below */
  var CONSENT_CATEGORIES = ["ad_storage", "analytics_storage", "ad_user_data",
    "ad_personalization"];
  /* Set to true to load GA for undecided and declining visitors as well, in a
     denied consent state (no cookies, only the consent signal Google needs for
     modelled traffic). Left false: nothing leaves the browser without a choice. */
  var LOAD_WITHOUT_CONSENT = false;
  var STYLE_ID = "llmrc-style";
  var PANEL_ID = "llmrc-panel";

  var own = doc.currentScript;
  var privacyHref = own ? own.getAttribute("data-privacy") || "" : "";
  var injected = false;

  function stored() {
    var value;
    try {
      value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "");
    } catch (err) {
      return null;
    }
    if (!value || typeof value !== "object") {
      return null;
    }
    if (value.state !== "granted" && value.state !== "denied" &&
        value.state !== "postponed") {
      return null;
    }
    return value;
  }

  function state() {
    var value = stored();
    if (!value) {
      return "";
    }
    if (value.state === "postponed" && !(Number(value.until) > Date.now())) {
      /* the quiet period elapsed, so the panel asks again */
      return "";
    }
    return value.state;
  }

  function remember(choice) {
    var value = {state: choice, at: Date.now()};
    if (choice === "postponed") {
      value.until = Date.now() + LATER_QUIET_PERIOD;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch (err) {
      /* private mode: the choice then lives for this page view only */
    }
  }

  /* ---- analytics loader ----------------------------------------------- */
  /* Parsing a snippet as text/html hoists <script>, <link> and <meta> into the
     parsed document's <head>, so the payload never lands in <body> alone. Both
     roots are scanned, head first, to keep the original snippet order. */
  function payloadNodes(parsed) {
    var nodes = [];
    [parsed.head, parsed.body].forEach(function (root) {
      if (!root) {
        return;
      }
      Array.prototype.slice.call(root.childNodes).forEach(function (node) {
        if (node.nodeType === 1) {
          nodes.push(node);
        }
      });
    });
    return nodes;
  }

  function inject(payload) {
    var parsed;
    try {
      parsed = new DOMParser().parseFromString(payload, "text/html");
    } catch (err) {
      return;
    }
    payloadNodes(parsed).forEach(function (node) {
      if (node.tagName.toLowerCase() === "script") {
        /* a cloned script stays inert until it is re-created in the document */
        var script = doc.createElement("script");
        Array.prototype.slice.call(node.attributes).forEach(function (attr) {
          script.setAttribute(attr.name, attr.value);
        });
        if (node.textContent) {
          script.textContent = node.textContent;
        }
        doc.head.appendChild(script);
      } else {
        doc.head.appendChild(doc.importNode(node, true));
      }
    });
  }

  function inlineScript(source) {
    var script = doc.createElement("script");
    script.textContent = source;
    doc.head.appendChild(script);
  }

  function consentDefaults(granted) {
    var pairs = CONSENT_CATEGORIES.map(function (name) {
      var value = granted && name === "analytics_storage" ? "granted" : "denied";
      return "'" + name + "':'" + value + "'";
    });
    return "window.dataLayer=window.dataLayer||[];" +
      "function gtag(){dataLayer.push(arguments)};" +
      "gtag('consent','default',{" + pairs.join(",") + "});";
  }

  /* The default is set before the payload so the first hit already carries the
     right state; the later update only covers a mid-page change of mind. */
  function loadAnalytics(granted) {
    if (!GA_PAYLOAD) {
      return;
    }
    if (injected) {
      if (granted) {
        inlineScript("gtag('consent','update',{'analytics_storage':'granted'});");
      }
      return;
    }
    injected = true;
    inlineScript(consentDefaults(granted));
    inject(GA_PAYLOAD);
  }

  /* ---- panel ---------------------------------------------------------- */
  var CSS = [
    ".llmrc{position:fixed;left:50%;bottom:18px;z-index:90;width:min(460px,calc(100vw - 28px));",
    "transform:translateX(-50%);box-sizing:border-box;display:flex;gap:14px;align-items:flex-start;",
    "padding:16px 18px;border:1px solid #1a232e;border-radius:12px;",
    "background:#0a0e14;box-shadow:0 18px 44px rgba(0,0,0,.55);color:#c6d3df;",
    "font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;",
    "font-size:13.5px;line-height:1.6;animation:llmrc-in .28s ease-out}",
    ".llmrc *{box-sizing:border-box}",
    ".llmrc:focus{outline:none}",
    "@keyframes llmrc-in{from{opacity:0;transform:translate(-50%,12px)}to{opacity:1;transform:translate(-50%,0)}}",
    "@media (prefers-reduced-motion: reduce){.llmrc{animation:none}}",
    ".llmrc h2{margin:0 0 6px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;",
    "letter-spacing:.16em;text-transform:uppercase;color:#00e59b;font-weight:600}",
    ".llmrc p{margin:0;color:#8492a3}",
    ".llmrc p b{color:#c6d3df;font-weight:600}",
    ".llmrc-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:13px}",
    ".llmrc button{appearance:none;border:1px solid #1f2c39;border-radius:8px;background:#0d131a;",
    "color:#c6d3df;font:inherit;font-size:12.5px;padding:8px 14px;cursor:pointer}",
    ".llmrc button:hover{border-color:#2c3d4d;color:#e8f1f9}",
    ".llmrc button[data-choice=\"granted\"]{border-color:#00e59b;background:#00e59b;color:#04120c;",
    "font-weight:600}",
    ".llmrc button[data-choice=\"granted\"]:hover{background:#22f0ac;color:#04120c}",
    ".llmrc a{color:#5aa9ff;font-size:12.5px;text-decoration:none}",
    ".llmrc a:hover{text-decoration:underline;text-underline-offset:3px}",
    ".llmrc-x{border:0 !important;background:transparent !important;color:#5a6778 !important;",
    "padding:0 4px !important;font-size:15px !important;line-height:1;order:-1;margin-left:auto !important}"
  ].join("\n");

  function addStyle() {
    if (doc.getElementById(STYLE_ID)) {
      return;
    }
    var style = doc.createElement("style");
    style.id = STYLE_ID;
    style.textContent = CSS;
    doc.head.appendChild(style);
  }

  function element(tag, className, inner) {
    var node = doc.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (inner != null) {
      node.innerHTML = inner;
    }
    return node;
  }

  function panel() {
    var box = element("div", "llmrc");
    box.id = PANEL_ID;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "false");
    box.setAttribute("aria-labelledby", "llmrc-title");
    box.setAttribute("aria-describedby", "llmrc-text");
    box.setAttribute("tabindex", "-1");

    var content = element("div");
    content.appendChild(element("h2", null, "Privacy &amp; cookies"));
    content.appendChild(element("p", null,
      "This site is static and serves no advertising. With your consent " +
      "<b>Google Analytics</b> records basic aggregate metrics (page views, " +
      "referring page, browser, country). Nothing is measured before you " +
      "choose, and the decision can be changed at any time."));

    var actions = element("div", "llmrc-actions");
    [["granted", "Accept analytics"], ["denied", "Decline"]].forEach(function (item) {
      var button = element("button", null, item[1]);
      button.type = "button";
      button.setAttribute("data-choice", item[0]);
      actions.appendChild(button);
    });
    if (privacyHref) {
      var link = element("a", null, "Privacy policy");
      link.href = privacyHref;
      actions.appendChild(link);
    }
    content.appendChild(actions);
    box.appendChild(content);

    var later = element("button", "llmrc-x", "&#10005;");
    later.type = "button";
    later.setAttribute("data-choice", "postponed");
    later.setAttribute("aria-label", "Decide later");
    later.title = "Ask me again in 30 days. Nothing is measured in the meantime.";
    box.appendChild(later);
    return box;
  }

  function current() {
    return doc.getElementById(PANEL_ID);
  }

  function open() {
    var existing = current();
    if (existing) {
      existing.focus();
      return;
    }
    addStyle();
    var box = panel();
    doc.body.appendChild(box);
    box.focus();
  }

  function close() {
    var existing = current();
    if (existing && existing.parentNode) {
      existing.parentNode.removeChild(existing);
    }
  }

  function decide(choice) {
    if (choice !== "granted" && choice !== "denied" && choice !== "postponed") {
      close();
      return;
    }
    remember(choice);
    close();
    if (choice === "granted") {
      loadAnalytics(true);
    }
  }

  /* ---- wiring --------------------------------------------------------- */
  var choice = state();
  if (choice === "granted") {
    loadAnalytics(true);
  } else {
    if (LOAD_WITHOUT_CONSENT) {
      loadAnalytics(false);
    }
    if (!choice) {
      open();
    }
  }

  doc.addEventListener("click", function (event) {
    var target = event.target && event.target.closest ? event.target : null;
    if (!target) {
      return;
    }
    if (target.closest("[data-consent-open]")) {
      event.preventDefault();
      open();
      return;
    }
    var choice = target.closest("[data-choice]");
    if (choice) {
      decide(choice.getAttribute("data-choice"));
    }
  });

  doc.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && current()) {
      close();
    }
  });

  window.llmRouterConsent = {
    state: function () {
      return state();
    },
    open: open,
    decide: decide
  };
})();
