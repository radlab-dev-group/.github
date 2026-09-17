# Documentation website

Everything you read under `/docs` is rendered from the Markdown files that
live in the **source repository** -- the llm-router checkout. This repository
hosts only the builder, the theme and the generated output; there is no second
copy of the documentation, no CMS and no server-side rendering:
`tools/build_docs.py` walks the Markdown in the source checkout, renders
static HTML and archives it per release. Publishing a document means
committing the `.md` file to the source repository.

The source checkout is resolved in this order: `--source`, then
`$LLM_ROUTER_DOCS_SOURCE`, then `[site] source_repo` in `tools/docs.toml`,
then this repository (legacy single-repo layout). Relative paths are resolved
against the current working directory.

```text
source repo (llm-router checkout)            pages repo (this repo)
---------------------------------            ------------------------
README.md                              ->   site/docs/overview.html
CHANGELOG.md                           ->   site/docs/changelog.html
llm_router_api/docs/*.md               ->   site/docs/1.0.6/llm-router-api/docs/*.html
.version + git tags                    ->   one frozen site/docs/<version>/ tree per release

tools/build_docs.py + tools/docs.toml    ->   the whole build (this README -> site/docs/website.html)
tools/theme/{docs.css,docs.js}           ->   site/docs/assets/
landing/index.html                       ->   site/index.html
```

Design constraints worth knowing before you touch anything:

- **Single source of truth** -- the source repository. Docs and code ship in
  the same commit, the same tag and the same PR; this repo never keeps a copy.
- **Static output only** -- plain HTML/CSS/JS, no bundler, no node_modules, no
  runtime. It can be served from any web server, object storage or GitHub Pages.
- **Versioned by git** -- `/docs` serves the version from the source repo's
  `.version`, every release tag of the source repo keeps a frozen copy of its
  own documentation.
- **All links relative** -- the site works under a project sub-path
  (`https://host/llm-router/docs/`) without any configuration.

## Layout

| Path | Role |
| --- | --- |
| `--source` path (llm-router checkout) | the source repo: Markdown, `.version`, git tags -- where the docs actually live |
| `tools/build_docs.py` | the whole builder: discovery, rendering, versioning, search, link check, preview server |
| `tools/docs.toml` | site metadata, discovery filters, navigation sections, per-page overrides |
| `tools/theme/docs.css` | the docs stylesheet: custom properties, sidebar/rail layout, responsive and print rules |
| `tools/theme/docs.js` | dependency-free 480-line IIFE: sidebar drawer, version switch, search, scroll spy, copy buttons |
| `tools/requirements-docs.txt` | `markdown` + `pygments`, the only build dependencies |
| `tools/README.md` | this document -- dogfooding the pipeline, published as `/docs/website.html` |
| `landing/index.html` | marketing landing page, copied verbatim to the site root |
| `gh-action/docs.yml` | CI template: build + deploy to GitHub Pages (two checkouts) |
| `site/` | build output -- never edited, never committed |

## Quick start

```bash
SRC=/path/to/llm-router                       # source repository checkout
python3 tools/build_docs.py --source $SRC --serve         # build .version, open http://localhost:8000/docs/
python3 tools/build_docs.py --source $SRC --check-links   # build and fail on broken internal links
python3 tools/build_docs.py --source $SRC --dry-run       # what would be published, write nothing
python3 tools/build_docs.py --source $SRC --all-versions  # every release tag + the current one (~1.5 min)
```

The builder bootstraps itself: if `markdown`/`pygments` are missing it creates
`.venv-docs/`, installs `tools/requirements-docs.txt` and re-execs into it. Use
`--no-bootstrap` in constrained environments, or install the requirements into
the interpreter you already use. Nothing outside `site/` and `.venv-docs/` is
written, and both are gitignored.

## What gets built

```text
site/
├── index.html                              landing page (copy of landing/index.html)
└── docs/
    ├── index.html                          hub of the newest build ("/docs")
    ├── versions.json                       published versions: entry, date, sha, page count
    ├── assets/{docs.css,docs.js,pygments.css}
    ├── 1.0.6/                              one directory tree per version
    │   ├── index.html                      section hub for that version
    │   ├── overview.html                   README.md
    │   ├── changelog.html                  CHANGELOG.md
    │   ├── llm-router-api/docs/...         sub-directories mirror the repo layout
    │   └── search.json                     client-side search index
    └── 0.1.0/ ...                          frozen documentation of older releases
```

Output paths mirror the source tree: directory names and file stems are
slugified (`llm_router_api/` → `llm-router-api/`), `README.md` becomes
`index.html`, and `unique_output()` resolves any remaining collision. Override
a path explicitly with `out` in `[[pages]]`.

## Versioning model

The versioning model follows the git state of the source repository (the
checkout behind `--source`):

- `.version` in the source repo is the current version and is published from
  the **working tree**, so uncommitted edits show up in your local preview.
- Tags (`v1.0.5`, `v0.9.4`, ...) are published from the tag object itself via
  `git ls-tree` / `git show`, never from disk -- an old release always renders
  the documentation that shipped with it.
- `/docs` and `/docs/<version>/` both render the same hub; the version dropdown
  (`#versions`) rewrites the path prefix, so switching from `1.0.6` to `0.1.0`
  jumps to the equivalent page whenever it exists in that release.
- Pre-release tags (`1.0.7-rc1`) are skipped unless `--include-prerelease` is
  set; `--max-versions N` caps the archive for faster CI runs.
- A partial build keeps previously published versions selectable: they are read
  back from `site/docs/versions.json`. Only `--clean` drops them.

The practical consequence: **cutting a release tag freezes the docs for that
release**. Nothing else to archive.

## Adding or changing a document

1. Write the `.md` file anywhere in the source repo (except an `exclude` path;
   hidden directories are skipped when scanning the working tree).
2. Commit it there. That is already enough -- a file that matches no section
   pattern lands in the fallback section (`other` → "Other docs"), so nothing
   can silently disappear from the site.
3. Optional: place it in a real section and give it a nicer title.

```toml
[[sections]]
id = "runbooks"
title = "Runbooks"
summary = "Step-by-step operational procedures."
match = ["docs/runbooks/**"]

[[pages]]
path = "docs/runbooks/rotate-keys.md"
title = "Rotating API keys"
order = 20
summary = "Zero downtime key rotation."
```

Section patterns are evaluated in declaration order and the first match wins,
so keep broad patterns (`**/*.md`) last. `--dry-run` prints the resulting
section/page tree before anything is written.

### `tools/docs.toml` reference

`[site]` -- `title`, `tagline`, `description`, `repo_url` (used for "edit on
GitHub" and for links to non-documentation files), `source_repo` (source
repository path; machine specific -- prefer `--source` or
`$LLM_ROUTER_DOCS_SOURCE`), `site_url` (canonical links; leave empty when
unpublished), `home_url` (target of the logo link back to the landing page,
relative to a version directory).

`[discover]`

| Key | Meaning |
| --- | --- |
| `include` | path-aware globs that become pages (default `**/*.md`) |
| `exclude` | never published -- `.git`, `.github`, virtualenvs, `site/`, `landing/`, caches |
| `fallback_section` | where unmatched files go, so a new doc is always reachable |

Globs are path aware: `*` stops at `/`, `**` spans directories, `?` is one
character. Matching is case sensitive against repo-relative paths.

`[[sections]]` -- `id` (used in the sidebar anchor), `title`, `summary` (hub
card text), `match` (list of globs).

`[[pages]]`

| Key | Default | Meaning |
| --- | --- | --- |
| `path` | required | repo-relative, case sensitive source path |
| `title` | first `#` heading | `<title>`, sidebar and breadcrumb label |
| `out` | derived from the source path | output path inside the version directory |
| `order` | `100` | position inside the section, then alphabetical by title |
| `summary` | the section `summary` | text on the hub card and in search results |
| `adapter` | none | preprocessor; `changelog` turns the flat `CHANGELOG.md` table into per-release sections |

## Markdown flavour

Python-Markdown with `fenced_code`, `codehilite`, `tables`, `def_list`,
`admonition` and `toc` (`toc_depth: 2-3`, `#` permalinks). Highlighting uses
the `one-dark` Pygments theme, compiled into `assets/pygments.css` at build
time -- no highlight.js at runtime.

There is **no front matter**: the title is the first `#` heading (a document
without one gets a title derived from its filename), and the hub card summary is
the `summary` of the section the document landed in. Use `[[pages]]` to set a
per-document title or summary.

Admonitions render as callouts:

```markdown
!!! warning "Rollback"
    Keep the previous tag available until the rollout is verified.
```

## Link rewriting

Relative links are rewritten per release, so the same Markdown works on GitHub
and on the site:

| Link target | Rendered as |
| --- | --- |
| a published `.md` file | URL of the generated page, anchor preserved (`#section`) |
| link without an extension (`docs/INSTALLATION`) | resolved with `.md` appended |
| repo-root-relative link from a subdirectory | resolved both relative to the page and to the repo root |
| a tracked, non-documentation file (source repo) | `https://github.com/…/blob/<ref>/<path>` |
| a directory | `https://github.com/…/tree/<ref>/<path>` |
| anything with a scheme (`http:`, `mailto:`) | untouched, plus `target="_blank" rel="noopener noreferrer"` |

`<ref>` is the branch or tag being rendered, so a v0.1.0 page links to the
v0.1.0 source. Targets that resolve to nothing are reported twice: a
`warning: unresolved link` line during the build, and a non-zero exit from
`--check-links`, which crawls every generated page for `href`/`src` with no
matching file. Keep `--check-links` on in CI.

## Search

Search is a static JSON index plus a few hundred lines of vanilla JS: no
backend, no third party script, nothing to crawl.

- `site/docs/<version>/search.json` holds `{version, pages:[{k, t, s, x, h, b}]}`
  -- output path, title, section, excerpt (240 plain chars), heading list and
  body text capped at 4000 chars.
- Matching is **AND**: every whitespace-separated token has to hit the page,
  otherwise the page is dropped. Weight per token: title 8, headings 3, section
  2, body 1; the ten highest scoring pages are shown, ties broken by path.
- Matches are highlighted with `<mark>` and the body snippet is a ~190 character
  window centred on the first hit.
- `/` focuses the field, `↑`/`↓` move through results, `Enter` opens the page,
  `Esc` closes and clears.
- Control the size with `--search all|latest|none`. A version index is ~110 KB,
  so all 42 archived versions cost ~3 MB; `latest` is the sane choice for a
  public mirror.

## Theme

`tools/theme/docs.css` is one custom-properties theme -- dark by design, with a
typographic scale, sidebar/content rail layout, four breakpoints and print rules
-- and `tools/theme/docs.js` is a dependency-free IIFE that only enhances markup
that is already readable without JavaScript. It binds to a small set of DOM ids --
`burger`, `sidebar`, `scrim`, `versions`, `search`, `q`, `results`, `dtoc`,
`main` -- produced by `SHELL_TEMPLATE` in the builder; change both sides
together. Layout is responsive from 320 px up to wide screens, with the sidebar
turning into an off-canvas drawer below the content breakpoint.

## Publishing (GitHub Pages)

`gh-action/docs.yml` is the CI template (copy it to the pages repository's
`.github/workflows/docs.yml`). It checks out **both** repositories -- the
pages repo and the llm-router source at `path: llm-router` -- and builds the
site from the source. It runs on pushes to `main` and on changes to
`builder/**`, `landing/**` or the workflow itself; PRs build without
deploying. Use `workflow_dispatch` to rebuild after a source release: release
tags live in the source repo, not here.

```bash
python -m pip install -r builder/tools/requirements-docs.txt
python builder/tools/build_docs.py --source llm-router --all-versions --check-links --output site
# site/ is uploaded as the Pages artifact
```

One-time setup: repository **Settings → Pages → Build and deployment →
Source = GitHub Actions**. The workflow needs `pages: write` and
`id-token: write` (already declared) and uses `concurrency.group: pages` so
overlapping pushes do not interleave deployments. Serving the site from another
host is a plain `cp -r site/ ...` -- or `python3 tools/build_docs.py --serve`
for a throwaway container.

## Runbook

| Symptom | Cause and fix |
| --- | --- |
| `N broken internal link(s)` | a relative link points at a path that does not exist in that release; fix the link or exclude the file |
| `warning: unresolved link in <file>` | link target missing at that ref; the link falls back to GitHub blob URL, so the page still renders |
| page missing from the sidebar | it is in an `exclude` path, or its section pattern is shadowed by an earlier `match` |
| wrong title on the hub | the document has no `#` heading, or a stale `[[pages]] title` |
| two documents fighting over one URL | same slug from different sources; set distinct `out` values |
| older versions missing from the dropdown | they were never built: run `--all-versions`, or `--clean` wiped `versions.json` |
| `source path is not a directory` | `--source` (or `$LLM_ROUTER_DOCS_SOURCE` / `source_repo`) points at the wrong place -- it must be the llm-router repo root, the directory with `.version` and the Markdown |
| `missing theme file` | `tools/theme/` incomplete -- both files are required |
| `the .venv-docs interpreter is missing markdown/pygments` | recreate it: `python3 -m venv .venv-docs && .venv-docs/bin/pip install -r tools/requirements-docs.txt` |
| `Address already in use` from `--serve` | another preview holds the port: `--port=8080` |

## Verifying a change locally

```bash
SRC=/path/to/llm-router
python3 tools/build_docs.py --source $SRC --clean --check-links   # expect: "internal links OK"
python3 tools/build_docs.py --source $SRC --serve --port=8080
```

Then check `/docs/` (hub), one generated page, the version dropdown at an old
release, and search at the root and inside a version directory. A rebuild after
moving a file should be a no-op for every other page.
