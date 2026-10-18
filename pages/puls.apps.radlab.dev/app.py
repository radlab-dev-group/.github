"""
Puls Informacji by RadLab — News Creator
Główna aplikacja Flask (Jinja2 + REST/AJAX proxy).
"""

import json
import logging
import os
import random
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
)
import requests

from i18n import LANGS, build_article_prompt, t
from markdown_utils import (
    format_crawled_date,
    format_when,
    host_of,
    reading_minutes,
    render_markdown_html,
    split_headline,
    word_count,
)

# Wczytanie zmiennych środowiskowych
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("puls-news-creator")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "radlab-puls-secret-key-2026")


# ==============================================================================
# Konfiguracja
# ==============================================================================

def load_app_config() -> dict[str, Any]:
    cfg_file = BASE_DIR / "config" / "config.json"
    file_cfg: dict[str, Any] = {}
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                file_cfg = json.load(f).get("news_creator", {})
        except Exception as e:
            logger.warning("Nie udało się odczytać config.json: %s", e)

    endpoints_cfg = file_cfg.get("endpoints", {})
    host = os.getenv("RADLAB_API_HOST", file_cfg.get("host", "http://192.168.100.79:8567")).strip().rstrip("/")
    ep_categories = os.getenv("RADLAB_EP_NEWS_CATEGORIES", endpoints_cfg.get("news_categories_with_pages", "api/public/news_categories_with_pages")).strip().lstrip("/")
    ep_search = os.getenv("RADLAB_EP_SEARCH_NEWS", endpoints_cfg.get("search_news", "api/public/search_news")).strip().lstrip("/")
    ep_generate = os.getenv("RADLAB_EP_GENERATE_ARTICLE", endpoints_cfg.get("generate_article", "api/public/generate_article_from_search")).strip().lstrip("/")
    predefined_path = os.getenv("RADLAB_PREDEFINED_QUERIES_PATH", file_cfg.get("predefined_queries_path", "kreator-pytania.txt")).strip()

    return {
        "host": host,
        "endpoints": {
            "news_categories_with_pages": ep_categories,
            "search_news": ep_search,
            "generate_article": ep_generate,
        },
        "predefined_queries_path": predefined_path,
    }


APP_CONFIG = load_app_config()


# ==============================================================================
# Filtry i pomocnicy Jinja2
# ==============================================================================

@app.context_processor
def inject_global_helpers():
    return {
        "t": t,
        "LANGS": LANGS,
        "host_of": host_of,
        "format_crawled_date": format_crawled_date,
        "format_when": format_when,
        "word_count": word_count,
        "reading_minutes": reading_minutes,
        "split_headline": split_headline,
        "render_markdown_html": render_markdown_html,
    }


@app.after_request
def add_security_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ==============================================================================
# Narzędzia backendowe i unwrap
# ==============================================================================

def unwrap_backend_response(payload: Any) -> tuple[bool, Any, str | None]:
    """Rozpakowanie koperty odpowiedzi radlab: {status: True, body: ...}."""
    if payload is None:
        return False, None, "Empty response from backend"

    if isinstance(payload, dict):
        if "status" in payload:
            if payload["status"] is True:
                return True, payload.get("body"), None
            return False, None, payload.get("error", "Backend reported an error.")
        return True, payload, None

    return False, None, str(payload)


def get_backend_url(endpoint_key: str) -> str:
    host = APP_CONFIG["host"]
    ep = APP_CONFIG["endpoints"].get(endpoint_key, endpoint_key)
    return f"{host}/{ep}"


def extract_sites(categories: dict[str, Any]) -> list[str]:
    """Ekstrakcja wszystkich adresów stron ze struktury kategorii."""
    sites: list[str] = []
    for cat_info in categories.values():
        for page in cat_info.get("category_pages", []):
            url = page.get("main_url")
            if url:
                sites.push(url) if hasattr(sites, "push") else sites.append(url)
    return sites


def derive_num_of_results(num_of_results: int, last_days: int) -> int:
    """Wyprowadzenie optymalnej liczby wyników."""
    if num_of_results > 0:
        return num_of_results
    if last_days == 1:
        return 7
    if last_days < 7:
        return 9
    return 12


def read_predefined_queries(count: int = 3) -> list[str]:
    """Wczytuje pytania z pliku i losuje zadaną liczbę unikalnych fraz."""
    p = Path(APP_CONFIG["predefined_queries_path"])
    if not p.is_absolute():
        p = BASE_DIR / p

    if not p.exists():
        return []

    try:
        with open(p, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        unique_queries = list(dict.fromkeys(lines))
        if not unique_queries:
            return []
        sample_count = min(count, len(unique_queries))
        return random.sample(unique_queries, sample_count)
    except Exception as e:
        logger.error("Błąd podczas odczytu predefiniowanych pytań: %s", e)
        return []


# ==============================================================================
# Endpointy aplikacji
# ==============================================================================

@app.route("/")
def index():
    """Główna strona aplikacji."""
    lang = request.args.get("lang", "pl")
    if lang not in ["pl", "en"]:
        lang = "pl"

    suggestions = read_predefined_queries(3)

    return render_template(
        "index.html",
        lang=lang,
        suggestions=suggestions,
    )


@app.route("/api/predefined-queries", methods=["GET"])
def api_predefined_queries():
    """Zwraca losowe predefiniowane pytania z pliku kreator-pytania.txt."""
    queries = read_predefined_queries(3)
    return jsonify({"queries": queries})


@app.route("/api/categories", methods=["GET"])
def api_categories():
    """Pobiera kategorie wraz z zaindeksowanymi stronami z backendu."""
    url = get_backend_url("news_categories_with_pages")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        raw_json = resp.json()
        ok, data, error = unwrap_backend_response(raw_json)
        if ok:
            return jsonify({"status": True, "body": data})
        return jsonify({"status": False, "error": error or "Nie udało się pobrać kategorii"}), 502
    except Exception as e:
        logger.error("Błąd pobierania kategorii z %s: %s", url, e)
        return jsonify({"status": False, "error": str(e)}), 502


@app.route("/api/search", methods=["POST"])
def api_search():
    """Wyszukiwanie newsów w bazie RADLAB."""
    data = request.get_json(silent=True) or request.form.to_dict()

    query = data.get("query") or data.get("text_to_search") or ""
    last_days = int(data.get("last_days") or data.get("number_of_last_days") or 1)
    num_of_results = int(data.get("num_of_results") or 0)
    num_of_results = derive_num_of_results(num_of_results, last_days)

    sites = data.get("sites")
    if isinstance(sites, list):
        sites_json = json.dumps(sites)
    elif isinstance(sites, str):
        sites_json = sites
    else:
        sites_json = json.dumps([])

    form_payload = {
        "text_to_search": query,
        "num_of_results": str(num_of_results),
        "number_of_last_days": str(last_days),
        "sites": sites_json,
    }

    url = get_backend_url("search_news")
    try:
        resp = requests.post(
            url,
            data=form_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )
        resp.raise_for_status()
        raw_json = resp.json()
        ok, body, error = unwrap_backend_response(raw_json)
        if ok:
            return jsonify({"status": True, "body": body})
        return jsonify({"status": False, "error": error or "Błąd wyszukiwania"}), 502
    except Exception as e:
        logger.error("Błąd wyszukiwania w %s: %s", url, e)
        return jsonify({"status": False, "error": str(e)}), 502


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Generowanie artykułu na podstawie znalezionych newsów."""
    data = request.get_json(silent=True) or request.form.to_dict()

    user_query = data.get("user_query") or data.get("query") or ""
    news_ids = data.get("news_ids") or []
    if isinstance(news_ids, str):
        try:
            news_ids_parsed = json.loads(news_ids)
        except Exception:
            news_ids_parsed = []
    else:
        news_ids_parsed = news_ids

    lang = data.get("lang", "pl")
    style = data.get("style", "simple")
    article_type = data.get("article_type") or build_article_prompt(lang, style)
    query_response_id = data.get("sse_query_response_id") or data.get("query_response_id") or "0"

    form_payload = {
        "user_query": user_query,
        "news_ids": json.dumps(news_ids_parsed),
        "article_type": article_type,
        "sse_query_response_id": str(query_response_id),
    }

    url = get_backend_url("generate_article")
    try:
        resp = requests.post(
            url,
            data=form_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=180,
        )
        resp.raise_for_status()
        raw_json = resp.json()
        ok, body, error = unwrap_backend_response(raw_json)
        if ok:
            # Przygotowanie wyrenderowanego HTML dla artykułu
            article_text = (
                body.get("article_str")
                or body.get("article")
                or body.get("new_article")
                or ""
            ) if isinstance(body, dict) else ""

            headline, content_body = split_headline(article_text)
            rendered_html = render_markdown_html(content_body)

            if isinstance(body, dict):
                body["headline"] = headline
                body["rendered_html"] = rendered_html
                body["word_count"] = word_count(article_text)
                body["reading_minutes"] = reading_minutes(article_text)
                body["formatted_when"] = format_when(body.get("when_generated"))

            return jsonify({"status": True, "body": body})

        return jsonify({"status": False, "error": error or "Błąd generowania artykułu"}), 502
    except Exception as e:
        logger.error("Błąd generowania artykułu w %s: %s", url, e)
        return jsonify({"status": False, "error": str(e)}), 502


@app.route("/api/proxy/<path:endpoint>", methods=["GET", "POST"])
def api_proxy(endpoint: str):
    """Uniwersalny proxy do backendu dla zachowania zgodności z API."""
    routes_map = {
        "news_categories_with_pages": "news_categories_with_pages",
        "search_news": "search_news",
        "generate_article": "generate_article",
    }
    target_key = routes_map.get(endpoint)
    if not target_key:
        return jsonify({"error": "Unknown proxy route"}), 404

    target_url = get_backend_url(target_key)
    try:
        if request.method == "GET":
            resp = requests.get(target_url, timeout=30)
        else:
            resp = requests.post(
                target_url,
                data=request.get_data(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=180,
            )
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get("content-type", "application/json"),
        )
    except Exception as e:
        return jsonify({"status": False, "error": f"Upstream failed: {e}"}), 502


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5200))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
