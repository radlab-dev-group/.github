# Documentation website

Everything you read under `/docs` is rendered from the Markdown files that live
in the **source repositories** -- the llm-router checkout and its satellite
repositories (llm-router-plugins, llm-router-services). This repository hosts
only the builder, the theme and the generated output; there is no second copy of
the documentation, no CMS and no server-side rendering: `tools/build_docs.py`
walks the Markdown in the source checkouts, renders static HTML and archives it
per release. Publishing a document means committing the `.md` file to the
appropriate source repository.

## Multi-repo layout

Three repositories feed the documentation site:

| Repository | Role | Versioning | URL prefix |
|---|---|---|---|
| `llm-router` | Core gateway docs | Per release tag (frozen archives) | `/docs/<version>/...` |
| `llm-router-plugins` | Maskers, guardrails, routing plugins | Independent release tags + latest stable mount | `/docs/plugins/<version>/...`, `/docs/plugins/...` |
| `llm-router-services` | HTTP services (guardrails, masker) | Independent release tags + latest stable mount | `/docs/services/<version>/...`, `/docs/services/...` |

Router, plugins and services releases are independent: each release tag gets a frozen copy
of its own Markdown. The topbar selects the router version; satellite selectors
live under their repository names in the left sidebar, including on `/docs`.
Switching within a repository keeps the same document when available, otherwise
it opens that release's documentation index. Plugin archives keep the shared
sidebar: only the plugin section uses the selected plugin release, while router
and services links remain available. The newest stable plugin tag is marked
`latest`; older tags are `archived`. There is no separate rolling option: the
unversioned satellite URLs use the newest stable tag, not uncommitted changes or
the development branch. Repositories without tags expose only `latest` from the
source checkout.
With JavaScript enabled, the chosen router, plugins and services versions travel together
in URL query parameters. Opening a plugin archive restores the selected router
menu instead of resetting it to latest, and vice versa. Each page still renders
its own repository's version from its archive path; query parameters only select
the other repository's navigation. The heading above the router menu and its
documentation index always follow the selected router version; satellite version
badges live in their own menu sections. Without JavaScript, static archive links
remain usable with the default navigation context.
Documentation index pages show separate `Router all versions` and
`Plugins all versions` and `Services all versions` panels. Each highlights its selected version, and links
switch only that project while preserving the other selection. Release details
are labeled with the project name (`Router release`, `Plugins release` or `Services release`).

Set `versions = "all"` in a satellite's `[[repos]]` entry to build its release
archives, or `versions = "latest"` for the latest tag only. Both satellite checkouts
must include tags (`git fetch --tags`; CI uses `fetch-depth: 0`). Router flags
`--all-versions` and `--max-versions` do not limit independent satellite archives.
`--include-prerelease` applies to all three repositories; latest still prefers a stable tag.

## Repository resolution

Sources are resolved in this order: CLI flags (`--source`, `--plugins`,
`--services`), environment variables (`LLM_ROUTER_DOCS_SOURCE`,
`LLM_ROUTER_PLUGINS_DOCS_SOURCE`, `LLM_ROUTER_SERVICES_DOCS_SOURCE`), then the
`[[repos]]` configuration in `tools/docs.toml`. For the primary (router)
repository, the builder falls back to this repository (legacy single-repo
layout) if no path is specified. Missing satellite repositories are skipped with
a warning -- they are optional.

```bash
python3 tools/build_docs.py --source /path/to/llm-router
python3 tools/build_docs.py --source /path/to/llm-router --plugins /path/to/plugins --services /path/to/services
python3 tools/build_docs.py --source /path/to/llm-router --all-versions
python3 tools/build_docs.py --serve          # build, then http://localhost:8000/docs/
```

`tools/build.sh` wraps all of this: it finds the three checkouts automatically,
runs the builder from the repository root and verifies the generated internal
links. Options are listed by `tools/build.sh --help`; per-machine paths go into
`tools/build.sh.conf` (shell, not committed), which can set `ROUTER_SRC`,
`PLUGINS_SRC`, `SERVICES_SRC` and `OUTPUT`.

## Design constraints

- **Single source of truth** -- the source repositories. Docs and code ship in
  the same commit, the same tag and the same PR; this repo never keeps a copy.
- **Static output only** -- plain HTML/CSS/JS, no bundler, no node_modules, no
  runtime. It can be served from any web server, object storage or GitHub Pages.
- **Versioned by git** -- router and plugins tags each keep their own frozen
  documentation; rolling satellite docs remain available separately.
- **All links relative** -- the site works under a project sub-path without
  configuration.
- **Cross-repo link map** -- links from one repository to documentation that
  moved to another are automatically resolved via `[[crosslinks]]` in
  `tools/docs.toml`.
- **GitHub commit links** -- every version reference, commit SHA, and "last
  commit" timestamp is rendered as a link to the corresponding GitHub URL.

## Layout

| Path | Role |
|---|---|
| `--source` path (llm-router checkout) | the source repo: Markdown, git tags |
| `--plugins` path (llm-router-plugins checkout) | tagged archives and rolling plugin documentation |
| `--services` path (llm-router-services checkout) | rolling services documentation |
| `tools/build_docs.py` | the whole builder: discovery, rendering, versioning, search, link check, preview server |
| `tools/build.sh` | wrapper: resolves the three checkouts, rebuilds the site, optional preview |
| `tools/docs.toml` | site metadata, discovery filters, navigation sections, per-page overrides, crosslinks |
| `tools/theme/docs.css` | the docs stylesheet |
| `tools/theme/docs.js` | client-side search, version switch, scroll spy, copy buttons |
| `tools/requirements-docs.txt` | `markdown` + `pygments`, the only build dependencies |
| `tools/README.md` | this document -- dogfooding the pipeline, published as `/docs/website.html` |
| `tools/tests/test_build_docs.py` | integration tests using temporary local Git repositories |
| `landing/index.html` | marketing landing page, copied verbatim to the site root |
| `gh-action/docs.yml` | CI template: build + deploy to GitHub Pages (three checkouts) |
| `site/` | build output -- never edited, never committed |

## Quick start

```bash
tools/build.sh                    # router + plugins + services, every release tag
tools/build.sh --latest           # newest router tag only (a few seconds)
tools/build.sh --fetch --clean    # refresh source tags, rebuild site/ from scratch
tools/build.sh --latest --serve   # rebuild and open http://localhost:8000/docs/
```

The builder can also be invoked directly:

```bash
SRC=/path/to/llm-router
PLUGINS=/path/to/llm-router-plugins
SERVICES=/path/to/llm-router-services

python3 tools/build_docs.py --source $SRC --plugins $PLUGINS --services $SERVICES --serve
```

## Adding a new document

Commit the `.md` file to the appropriate source repository. That is all -- files
that do not match any `[[sections]]` pattern land in that repository's
`fallback_section`, so nothing can silently disappear from the site. Use
`[[pages]]` to pick a nicer title/summary/position.

## Navigation sections

Sections are declared in `[[sections]]` in `tools/docs.toml`, evaluated in
order; the first matching glob wins. Each section belongs to one repository
(`repo` field, default `"router"`). Sections for one repository must be
contiguous in the configuration file.

## Per-document overrides

The `[[pages]]` array overrides title, output filename, sort order, summary and
markdown adapter for a specific document. `path` is repository-relative and
case sensitive. The `repo` field disambiguates when the same path exists in
multiple repositories.

```toml
[[pages]]
path = "README.md"
repo = "plugins"
title = "Plugins overview"
out = "index.html"
order = 10
```

## Cross-repo link map

When documentation moves between repositories, links from the old location can
be automatically rewritten using `[[crosslinks]]`:

```toml
[[crosslinks]]
from = "README.md"
link = "llm_router_api/README.md#masking--guardrail"
to = "plugins:README.md#1-anonymizers-maskers"
```

The `from` field is optional (glob, default: any). The `link` field must match
the link exactly as written in the source document (relative path or full
GitHub URL). The `to` field is `"<repo-id>:<repo-relative-path>[#anchor]"`.
If the target page is not built for the current version, normal resolution
(GitHub blob fallback) applies.

## Commit links

Every version reference, commit SHA, and "last commit" timestamp is rendered as
a link to the corresponding GitHub URL:

- Topbar footer: version links to the tree, SHA links to the commit
- Page metadata: "built from" shows ref (tree link) and SHA (commit link)
- "Last commit" links to the exact commit that last modified the file
- Hub hero and sidebar: commit links for each repository

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| page missing from the sidebar | it is in an `exclude` path, or its section pattern is shadowed by an earlier `match` |
| link is a GitHub blob URL | the target does not exist as a documentation page; the builder falls back to the raw file |
| search is empty | the `search.json` index was not built for this version (check `--search` flag) |
| `--check-links` fails on external URLs | the checker only validates internal links; external URLs are not followed |
