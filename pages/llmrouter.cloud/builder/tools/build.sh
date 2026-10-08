#!/usr/bin/env bash
#
# Rebuild the llm-router documentation site: router + plugins + services.
#
#   tools/build.sh              # every router tag, satellites included
#   tools/build.sh --latest     # newest router tag only (fast)
#   tools/build.sh --serve      # rebuild, then preview on http://localhost:8000
#   tools/build.sh --fetch --all-versions
#
# Source checkouts are resolved in this order:
#   CLI flag (--source/--plugins/--services)
#   environment (LLM_ROUTER_DOCS_SOURCE, LLM_ROUTER_PLUGINS_DOCS_SOURCE,
#                LLM_ROUTER_SERVICES_DOCS_SOURCE, LLM_ROUTER_DOCS_OUTPUT)
#   tools/build.sh.conf (machine specific, not committed)
#   automatic search of the directories around this repository
# A missing satellite is a warning (its docs are skipped); a missing router
# checkout aborts the build.
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILDER="$SCRIPT_DIR/build_docs.py"
CONF_FILE="$SCRIPT_DIR/build.sh.conf"
SEARCH_BASES_READY=0

# --- defaults ---------------------------------------------------------------
ROUTER_SRC="${LLM_ROUTER_DOCS_SOURCE:-}"
PLUGINS_SRC="${LLM_ROUTER_PLUGINS_DOCS_SOURCE:-}"
SERVICES_SRC="${LLM_ROUTER_SERVICES_DOCS_SOURCE:-}"
OUTPUT="${LLM_ROUTER_DOCS_OUTPUT:-$REPO_ROOT/site}"

ALL_VERSIONS=1
MAX_VERSIONS=""
CLEAN=0
CHECK_LINKS=1
DRY_RUN=0
SERVE=0
PORT=8000
SKIP_PLUGINS=0
SKIP_SERVICES=0
FETCH_TAGS=0
PULL_SOURCES=0
QUIET=0

usage() {
  cat <<'USAGE'
Rebuild the llm-router documentation site (router + plugins + services).

Sources:
  -s, --source PATH      llm-router checkout            [env LLM_ROUTER_DOCS_SOURCE]
  -p, --plugins PATH     llm-router-plugins checkout    [env LLM_ROUTER_PLUGINS_DOCS_SOURCE]
  -S, --services PATH    llm-router-services checkout   [env LLM_ROUTER_SERVICES_DOCS_SOURCE]
  -o, --output DIR       site directory                 [default <repo>/site]
      --router-only      router docs only (shorthand for the two flags below)
      --no-plugins       skip the plugins satellite
      --no-services      skip the services satellite

Versions:
  -a, --all-versions     every router release tag (default)
      --latest           newest router tag only
  -n, --max-versions N   newest N router tags
      --prerelease       include pre-release tags (default: no)

Options:
  -c, --clean            delete site/docs before building
  -f, --fetch            git fetch --tags --prune in every source checkout
  -u, --pull             git pull --ff-only when a checkout is clean
  -l, --check-links      fail on broken internal links (default: on)
      --no-check-links   skip the internal link checker
  -r, --serve            serve the built site after rebuilding
      --port N           preview port [default 8000]
      --dry-run          show what would be written, change nothing
  -q, --quiet            only warnings and errors
  -h, --help             this help

Examples:
  tools/build.sh --fetch                 # refresh tags, rebuild every archive
  tools/build.sh --latest --serve        # quick rebuild + preview
  tools/build.sh -p ~/work/llm-router-plugins --no-check-links
USAGE
}

# optional local overrides: source paths, default output, extra flags
if [ -f "$CONF_FILE" ]; then
  # shellcheck disable=SC1090
  . "$CONF_FILE"
fi

if [ -t 1 ]; then
  C_INFO=$'\033[1;34m'; C_WARN=$'\033[1;33m'; C_DIM=$'\033[2m'; C_OFF=$'\033[0m'
else
  C_INFO=""; C_WARN=""; C_DIM=""; C_OFF=""
fi

info() { [ "$QUIET" -eq 1 ] || printf '%s\n' "${C_INFO}$*${C_OFF}"; }
dim() { [ "$QUIET" -eq 1 ] || printf '%s\n' "${C_DIM}$*${C_OFF}"; }
warn() { printf '%s\n' "${C_WARN}warning: $*${C_OFF}" >&2; }
die() { printf '%s\n' "${C_WARN}error: $*${C_OFF}" >&2; exit 2; }

# --- argument parsing -------------------------------------------------------
PRERELEASE=0
while [ $# -gt 0 ]; do
  case "$1" in
    -s|--source)        ROUTER_SRC="${2:?--source needs a path}"; shift 2 ;;
    -p|--plugins)       PLUGINS_SRC="${2:?--plugins needs a path}"; shift 2 ;;
    -S|--services)      SERVICES_SRC="${2:?--services needs a path}"; shift 2 ;;
    -o|--output)        OUTPUT="${2:?--output needs a path}"; shift 2 ;;
    --router-only)      SKIP_PLUGINS=1; SKIP_SERVICES=1; shift ;;
    --no-plugins)       SKIP_PLUGINS=1; shift ;;
    --no-services)      SKIP_SERVICES=1; shift ;;
    -a|--all-versions)  ALL_VERSIONS=1; MAX_VERSIONS=""; shift ;;
    --latest)           ALL_VERSIONS=0; MAX_VERSIONS=1; shift ;;
    -n|--max-versions)  MAX_VERSIONS="${2:?--max-versions needs a number}"; ALL_VERSIONS=0; shift 2 ;;
    --prerelease)       PRERELEASE=1; shift ;;
    -c|--clean)         CLEAN=1; shift ;;
    -f|--fetch)         FETCH_TAGS=1; shift ;;
    -u|--pull)          FETCH_TAGS=1; PULL_SOURCES=1; shift ;;
    -l|--check-links)   CHECK_LINKS=1; shift ;;
    --no-check-links)   CHECK_LINKS=0; shift ;;
    -r|--serve)         SERVE=1; shift ;;
    --port)             PORT="${2:?--port needs a number}"; shift 2 ;;
    --dry-run)          DRY_RUN=1; shift ;;
    -q|--quiet)         QUIET=1; shift ;;
    -h|--help)          usage; exit 0 ;;
    *)                  die "unknown option: $1 (see --help)" ;;
  esac
done

[ -f "$BUILDER" ] || die "builder not found: $BUILDER"

# --- source resolution ------------------------------------------------------
# Directories that may hold the llm-router* checkouts, most specific first.
search_bases() {
  local dir="$REPO_ROOT" level base
  SEARCH_BASES=()
  if [ -n "${LLM_ROUTER_DOCS_WORKSPACE:-}" ]; then
    SEARCH_BASES+=("$LLM_ROUTER_DOCS_WORKSPACE")
  fi
  for level in 1 2 3 4 5; do
    dir="$(dirname "$dir")"
    SEARCH_BASES+=("$dir")
  done
  for base in "$HOME" "$HOME/dev" "$HOME/src" "$HOME/projects" "$HOME/work" "$HOME/workspace"; do
    SEARCH_BASES+=("$base")
  done
  SEARCH_BASES_READY=1
}

find_checkout() { # <checkout name> -- prints the first match
  local name="$1" base
  [ "$SEARCH_BASES_READY" -eq 1 ] || search_bases
  for base in ${SEARCH_BASES[@]+"${SEARCH_BASES[@]}"}; do
    if [ -n "$base" ] && [ -d "$base/$name/.git" ]; then
      printf '%s\n' "$base/$name"
      return 0
    fi
  done
  return 1
}

resolve_source() { # <repo id> <checkout name> <current value>
  local id="$1" name="$2" value="$3" found
  if [ -n "$value" ]; then
    found="$value"
  else
    found="$(find_checkout "$name" || true)"
  fi
  if [ -z "$found" ]; then
    if [ "$id" = "router" ]; then
      die "llm-router checkout not found. Pass --source /path/to/llm-router,
  set LLM_ROUTER_DOCS_SOURCE, or write it into ${CONF_FILE}:
    LLM_ROUTER_DOCS_SOURCE=/path/to/llm-router"
    fi
    return 1
  fi
  case "$found" in
    "~"*) found="${HOME}${found#\~}" ;;
  esac
  if [ ! -d "$found" ]; then
    if [ "$id" = "router" ]; then
      die "source path is not a directory: $found"
    fi
    return 1
  fi
  ( cd "$found" && pwd -P )
}

ROUTER_SRC="$(resolve_source router llm-router "$ROUTER_SRC")"
if [ "$SKIP_PLUGINS" -eq 1 ]; then
  PLUGINS_SRC=""
else
  PLUGINS_SRC="$(resolve_source plugins llm-router-plugins "$PLUGINS_SRC" || true)"
  [ -n "$PLUGINS_SRC" ] || warn "llm-router-plugins checkout not found, plugin docs will be skipped"
fi
if [ "$SKIP_SERVICES" -eq 1 ]; then
  SERVICES_SRC=""
else
  SERVICES_SRC="$(resolve_source services llm-router-services "$SERVICES_SRC" || true)"
  [ -n "$SERVICES_SRC" ] || warn "llm-router-services checkout not found, services docs will be skipped"
fi

# --- optional source sync ---------------------------------------------------
sync_checkout() { # <label> <path>
  local label="$1" path="$2" branch
  if ! git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    warn "$label is not a git checkout, not syncing: $path"
    return 0
  fi
  branch="$(git -C "$path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"
  if [ "$PULL_SOURCES" -eq 1 ] && [ -z "$(git -C "$path" status --porcelain)" ]; then
    info "Pulling $label ($branch)"
    git -C "$path" pull --ff-only
    git -C "$path" fetch --tags --prune || warn "fetching tags for $label failed"
  else
    if [ "$PULL_SOURCES" -eq 1 ]; then
      warn "$label has local changes, pulling skipped -- fetching tags only"
    else
      info "Fetching tags for $label"
    fi
    git -C "$path" fetch --tags --prune || warn "fetching tags for $label failed"
  fi
}

if [ "$FETCH_TAGS" -eq 1 ]; then
  sync_checkout router "$ROUTER_SRC"
  [ -n "$PLUGINS_SRC" ] && sync_checkout plugins "$PLUGINS_SRC"
  [ -n "$SERVICES_SRC" ] && sync_checkout services "$SERVICES_SRC"
fi

# --- interpreter ------------------------------------------------------------
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ] && [ -x "$REPO_ROOT/.venv-docs/bin/python" ]; then
  PYTHON="$REPO_ROOT/.venv-docs/bin/python"
fi

# --- build ------------------------------------------------------------------
cmd=("$PYTHON" "$BUILDER" --source "$ROUTER_SRC" --output "$OUTPUT")
[ -n "$PLUGINS_SRC" ] && cmd+=(--plugins "$PLUGINS_SRC")
[ -n "$SERVICES_SRC" ] && cmd+=(--services "$SERVICES_SRC")
if [ -n "$MAX_VERSIONS" ]; then
  cmd+=(--max-versions "$MAX_VERSIONS")
elif [ "$ALL_VERSIONS" -eq 1 ]; then
  cmd+=(--all-versions)
fi
[ "$PRERELEASE" -eq 1 ] && cmd+=(--include-prerelease)
[ "$CLEAN" -eq 1 ] && cmd+=(--clean)
# the checker validates the generated HTML, so a dry run has nothing to check
if [ "$CHECK_LINKS" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
  cmd+=(--check-links)
fi
[ "$DRY_RUN" -eq 1 ] && cmd+=(--dry-run)
[ "$QUIET" -eq 1 ] && cmd+=(--quiet)

info "Building the docs site"
dim "  router    $ROUTER_SRC"
dim "  plugins   ${PLUGINS_SRC:-skipped}"
dim "  services  ${SERVICES_SRC:-skipped}"
dim "  output    $OUTPUT"
if [ -n "$MAX_VERSIONS" ]; then
  dim "  versions  newest $MAX_VERSIONS"
elif [ "$ALL_VERSIONS" -eq 1 ]; then
  dim "  versions  every release tag"
else
  dim "  versions  latest only"
fi
dim "  \$ ${cmd[*]}"

status=0
# The builder is run from the repository root so that relative paths, the
# landing page and the .venv-docs bootstrap all resolve the same way CI does.
( cd "$REPO_ROOT" && "${cmd[@]}" ) || status=$?

if [ "$status" -eq 0 ]; then
  if [ "$DRY_RUN" -eq 1 ]; then
    info "Dry run finished, nothing written."
  else
    pages=$(find "$OUTPUT/docs" -name '*.html' 2>/dev/null | wc -l | tr -d ' ')
    info "Site rebuilt: ${pages} HTML pages in ${OUTPUT}"
    dim  "  open: http://localhost:$PORT/docs/  (tools/build.sh --serve builds and serves)"
  fi

  if [ "$SERVE" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
    info "Serving ${OUTPUT} on http://127.0.0.1:${PORT}/docs/ -- press Ctrl+C to stop"
    ( cd "$OUTPUT" && exec "$PYTHON" -m http.server "$PORT" ) \
      || warn "preview server stopped: port $PORT is busy or cannot be bound"
  fi
else
  printf '%s\n' "${C_WARN}error: builder failed with exit code ${status}${C_OFF}" >&2
fi

exit "$status"
