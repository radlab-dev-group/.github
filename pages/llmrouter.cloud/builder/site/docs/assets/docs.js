/* ==========================================================================
   llm-router /docs -- progressive enhancement only.
   Every page is readable with JavaScript disabled; this file adds the drawer,
   the client side search over search.json, scroll spy and copy buttons.
   No dependencies, no build step: the builder copies it verbatim.
   ========================================================================== */
(function () {
  "use strict";

  var doc = document;
  var body = doc.body;

  function all(selector, root) {
    return Array.prototype.slice.call((root || doc).querySelectorAll(selector));
  }

  function text(value) {
    return String(value == null ? "" : value);
  }

  function escapeHtml(value) {
    return text(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ---- sidebar drawer (narrow viewports) ----------------------------- */
  function initDrawer() {
    var burger = doc.getElementById("burger");
    var sidebar = doc.getElementById("sidebar");
    var scrim = doc.getElementById("scrim");
    if (!burger || !sidebar) {
      return;
    }

    function setOpen(open) {
      sidebar.classList.toggle("open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      if (scrim) {
        scrim.hidden = !open;
      }
      body.classList.toggle("drawer-open", open);
    }

    burger.addEventListener("click", function () {
      setOpen(!sidebar.classList.contains("open"));
    });

    if (scrim) {
      scrim.addEventListener("click", function () {
        setOpen(false);
      });
    }

    sidebar.addEventListener("click", function (event) {
      var link = event.target && event.target.closest ? event.target.closest("a") : null;
      if (link && window.matchMedia("(max-width: 979px)").matches) {
        setOpen(false);
      }
    });

    doc.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sidebar.classList.contains("open")) {
        setOpen(false);
        burger.focus();
      }
    });

    window.addEventListener("resize", function () {
      if (!window.matchMedia("(max-width: 979px)").matches) {
        setOpen(false);
      }
    });
  }

  /* ---- version switcher ---------------------------------------------- */
  function initVersions() {
    var select = doc.getElementById("versions");
    if (!select) {
      return;
    }
    select.addEventListener("change", function () {
      var target = select.value;
      if (target) {
        window.location.href = target;
      }
    });
  }

  /* ---- code blocks: copy button -------------------------------------- */
  function legacyCopy(value) {
    var area = doc.createElement("textarea");
    area.value = value;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    body.appendChild(area);
    area.select();
    try {
      doc.execCommand("copy");
    } catch (error) {
      return false;
    }
    body.removeChild(area);
    return true;
  }

  function initCopyButtons() {
    var blocks = all("article.prose .codehilite");
    if (!blocks.length) {
      return;
    }
    blocks.forEach(function (block) {
      var button = doc.createElement("button");
      button.type = "button";
      button.className = "copy";
      button.textContent = "copy";
      button.addEventListener("click", function () {
        var code = text(block.textContent).replace(/^\s*copy\s*/, "");
        var done = function (ok) {
          button.textContent = ok ? "copied" : "failed";
          button.classList.add("done");
          window.setTimeout(function () {
            button.textContent = "copy";
            button.classList.remove("done");
          }, 1600);
        };
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(code).then(
            function () {
              done(true);
            },
            function () {
              done(legacyCopy(code));
            }
          );
        } else {
          done(legacyCopy(code));
        }
      });
      block.appendChild(button);
    });
  }

  /* ---- wide tables get a horizontal scroller ------------------------- */
  function initTables() {
    all("article.prose table").forEach(function (table) {
      if (table.parentElement && table.parentElement.classList.contains("tablewrap")) {
        return;
      }
      var wrap = doc.createElement("div");
      wrap.className = "tablewrap";
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
  }

  /* ---- scroll spy for the right rail --------------------------------- */
  function initScrollSpy() {
    var rail = doc.getElementById("dtoc");
    if (!rail) {
      return;
    }
    var links = all('a[href^="#"]', rail);
    if (!links.length) {
      return;
    }
    var watched = [];
    links.forEach(function (link) {
      var target = doc.getElementById(decodeURIComponent(link.getAttribute("href").slice(1)));
      if (target) {
        watched.push({ link: link, el: target });
      }
    });
    if (!watched.length) {
      return;
    }

    function update() {
      var offset = 96;
      var active = watched[0];
      for (var i = 0; i < watched.length; i += 1) {
        if (watched[i].el.getBoundingClientRect().top - offset <= 0) {
          active = watched[i];
        }
      }
      var atBottom =
        window.innerHeight + window.scrollY >= doc.documentElement.scrollHeight - 4;
      if (atBottom) {
        active = watched[watched.length - 1];
      }
      watched.forEach(function (item) {
        item.link.classList.toggle("on", item === active);
      });
    }

    var ticking = false;
    window.addEventListener(
      "scroll",
      function () {
        if (ticking) {
          return;
        }
        ticking = true;
        window.requestAnimationFrame(function () {
          ticking = false;
          update();
        });
      },
      { passive: true }
    );
    window.addEventListener("resize", update);
    update();
  }

  /* ---- client side search over the per-version index ------------------ */
  function initSearch() {
    var form = doc.getElementById("search");
    var input = doc.getElementById("q");
    var box = doc.getElementById("results");
    if (!form || !input || !box) {
      return;
    }
    var indexUrl = body.getAttribute("data-search") || "";
    if (!indexUrl) {
      form.hidden = true;
      return;
    }

    /* page keys in the index are relative to the directory holding the index */
    var base = indexUrl.slice(0, indexUrl.lastIndexOf("/") + 1);
    var index = null;
    var loading = null;
    var hits = [];
    var cursor = -1;

    function pageHref(page) {
      return escapeHtml(base + text(page.k));
    }

    function load() {
      if (index) {
        return Promise.resolve(index);
      }
      if (!loading) {
        loading = fetch(indexUrl, { cache: "no-cache" })
          .then(function (response) {
            if (!response.ok) {
              throw new Error("search index unavailable");
            }
            return response.json();
          })
          .then(function (data) {
            index = data && data.pages ? data.pages : [];
            return index;
          })
          .catch(function () {
            loading = null;
            return [];
          });
      }
      return loading;
    }

    function highlight(value, tokens) {
      var out = escapeHtml(value);
      tokens.forEach(function (token) {
        if (!token) {
          return;
        }
        var pattern = new RegExp("(" + token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
        out = out.replace(pattern, "<mark>$1</mark>");
      });
      return out;
    }

    function window_around(value, token) {
      var haystack = value.toLowerCase();
      var at = token ? haystack.indexOf(token) : -1;
      if (at < 0) {
        return value.slice(0, 170);
      }
      var from = Math.max(0, at - 62);
      var slice = value.slice(from, from + 190);
      return (from > 0 ? "…" : "") + slice + (from + 190 < value.length ? "…" : "");
    }

    function score(pages, tokens) {
      var found = [];
      pages.forEach(function (page) {
        var title = text(page.t).toLowerCase();
        var section = text(page.s).toLowerCase();
        var headings = (page.h || []).join(" \u00b7 ").toLowerCase();
        var bodyText = text(page.b);
        var lowerBody = bodyText.toLowerCase();
        var total = 0;
        var matched = true;
        for (var i = 0; i < tokens.length; i += 1) {
          var token = tokens[i];
          var here = 0;
          if (title.indexOf(token) >= 0) {
            here += 8;
          }
          if (headings.indexOf(token) >= 0) {
            here += 3;
          }
          if (section.indexOf(token) >= 0) {
            here += 2;
          }
          if (lowerBody.indexOf(token) >= 0) {
            here += 1;
          }
          if (!here) {
            matched = false;
            break;
          }
          total += here;
        }
        if (matched) {
          found.push({ page: page, total: total, body: bodyText });
        }
      });
      found.sort(function (left, right) {
        if (right.total !== left.total) {
          return right.total - left.total;
        }
        return text(left.page.k).localeCompare(text(right.page.k));
      });
      return found.slice(0, 10);
    }

    function render(query) {
      var tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
      if (!tokens.length) {
        hide();
        return;
      }
      hits = score(index || [], tokens);
      var markup = hits.map(function (hit, position) {
        var page = hit.page;
        var href = pageHref(page);
        var snippet = window_around(hit.body || text(page.x), tokens[0]);
        return (
          '<a class="res' +
          (position === cursor ? " on" : "") +
          '" href="' +
          escapeHtml(href) +
          '" role="option" aria-selected="' +
          (position === cursor ? "true" : "false") +
          '"><span class="res-t">' +
          highlight(page.t, tokens) +
          '</span><span class="res-s">' +
          escapeHtml(page.s) +
          '</span><span class="res-x">' +
          highlight(snippet, tokens) +
          "</span></a>"
        );
      });
      if (!markup.length) {
        markup.push(
          '<div class="res none">no match for &ldquo;' +
            escapeHtml(query) +
            "&rdquo; in v" +
            escapeHtml(body.getAttribute("data-version")) +
            "</div>"
        );
      }
      markup.push(
        '<div class="res-foot mono">' +
          hits.length +
          (hits.length === 1 ? " result" : " results") +
          " &middot; &uarr;&darr; to move &middot; enter to open</div>"
      );
      box.innerHTML = markup.join("");
      box.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }

    function hide() {
      box.hidden = true;
      box.innerHTML = "";
      hits = [];
      cursor = -1;
      input.setAttribute("aria-expanded", "false");
    }

    function move(step) {
      if (!hits.length) {
        return;
      }
      cursor = (cursor + step + hits.length) % hits.length;
      render(input.value.trim());
      var current = box.querySelector(".res.on");
      if (current && current.scrollIntoView) {
        current.scrollIntoView({ block: "nearest" });
      }
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var target = hits[cursor < 0 ? 0 : cursor];
      if (target) {
        window.location.href = pageHref(target.page);
      }
    });

    input.addEventListener("input", function () {
      var query = input.value.trim();
      if (query.length < 2) {
        hide();
        form.classList.remove("busy");
        return;
      }
      form.classList.add("busy");
      cursor = -1;
      load().then(function () {
        form.classList.remove("busy");
        if (query === input.value.trim()) {
          render(query);
        }
      });
    });

    input.addEventListener("focus", function () {
      if (input.value.trim().length >= 2) {
        render(input.value.trim());
      }
    });

    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        move(1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        move(-1);
      } else if (event.key === "Escape") {
        input.value = "";
        hide();
      }
    });

    doc.addEventListener("keydown", function (event) {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      var tag = (doc.activeElement && doc.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        return;
      }
      event.preventDefault();
      input.focus();
      input.select();
    });

    doc.addEventListener("click", function (event) {
      if (!form.contains(event.target)) {
        hide();
      }
    });

    input.addEventListener("blur", function () {
      window.setTimeout(function () {
        if (!form.contains(doc.activeElement)) {
          hide();
        }
      }, 120);
    });
  }

  function init() {
    initDrawer();
    initVersions();
    initCopyButtons();
    initTables();
    initScrollSpy();
    initSearch();
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
