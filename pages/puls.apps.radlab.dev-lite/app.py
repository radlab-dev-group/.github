"""
Puls Informacji — Lekki kreator artykułów RAG z indeksu newsów RadLab.
Flask application serving the frontend and proxying requests to the RadLab API.
"""

import json
import os
import random
import requests
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    abort,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get("CONFIG_PATH", os.path.join(BASE_DIR, "config", "config.json"))

app = Flask(__name__, template_folder="templates", static_folder="static")


# ===================== Config =====================

def load_config() -> dict:
    """Load configuration from JSON file or defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "rt", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {
        "news_creator": {
            "host": "http://192.168.100.79:8567",
            "endpoints": {
                "news_categories_with_pages": "api/public/news_categories_with_pages",
                "search_news": "api/public/search_news",
                "generate_article": "api/public/generate_article_from_search"
            },
            "predefined_queries_path": "kreator-pytania.txt"
        }
    }


def get_api_config() -> dict:
    """Build API configuration resolving environment variables."""
    cfg = load_config().get("news_creator", {})
    host = os.environ.get("RADLAB_API_HOST", cfg.get("host", "http://192.168.100.79:8567")).rstrip("/")
    endpoints = cfg.get("endpoints", {})

    ep_cats = os.environ.get("RADLAB_EP_NEWS_CATEGORIES", endpoints.get("news_categories_with_pages", "api/public/news_categories_with_pages")).lstrip("/")
    ep_search = os.environ.get("RADLAB_EP_SEARCH_NEWS", endpoints.get("search_news", "api/public/search_news")).lstrip("/")
    ep_gen = os.environ.get("RADLAB_EP_GENERATE_ARTICLE", endpoints.get("generate_article", "api/public/generate_article_from_search")).lstrip("/")
    queries_path = os.environ.get("RADLAB_PREDEFINED_QUERIES_PATH", cfg.get("predefined_queries_path", "kreator-pytania.txt"))

    if not os.path.isabs(queries_path):
        queries_path = os.path.join(BASE_DIR, queries_path)

    return {
        "host": host,
        "endpoints": {
            "news_categories_with_pages": ep_cats,
            "search_news": ep_search,
            "generate_article": ep_gen,
        },
        "urls": {
            "news_categories_with_pages": f"{host}/{ep_cats}",
            "search_news": f"{host}/{ep_search}",
            "generate_article": f"{host}/{ep_gen}",
        },
        "predefined_queries_path": queries_path,
    }


# ===================== Helpers =====================

def _unwrap_response(raw: dict | list | str | int | float | bool | None) -> dict:
    """Unwrap standard RadLab API envelope: {status: true, body: ...} -> body."""
    if isinstance(raw, dict):
        if "status" in raw and isinstance(raw["status"], bool):
            if raw["status"]:
                return {"ok": True, "data": raw.get("body")}
            return {"ok": False, "error": raw.get("error", "Backend reported an error.")}
        return {"ok": True, "data": raw}
    if raw is None:
        return {"ok": False, "error": "Empty response"}
    return {"ok": False, "error": str(raw)}


def _call_backend_get(url: str, timeout: int = 30) -> dict:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return _unwrap_response(resp.json())
    except requests.RequestException as err:
        return {"ok": False, "error": f"Connection error: {str(err)}"}
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid JSON response from backend"}


def _call_backend_post(url: str, form_data: dict, timeout: int = 180) -> dict:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        resp = requests.post(url, data=form_data, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return _unwrap_response(resp.json())
    except requests.RequestException as err:
        return {"ok": False, "error": f"Connection error: {str(err)}"}
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid JSON response from backend"}


# ===================== Predefined Queries =====================

def load_predefined_queries(count: int = 3) -> list[str]:
    """Read queries from file, deduplicate, and pick random subset."""
    api_cfg = get_api_config()
    path = api_cfg["predefined_queries_path"]
    if not os.path.exists(path):
        return []

    try:
        with open(path, "rt", encoding="utf-8") as fh:
            lines = fh.readlines()
    except Exception:
        return []

    seen = set()
    queries = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        queries.append(cleaned)

    if not queries:
        return []

    random.shuffle(queries)
    return queries[:count]


# ===================== Routes =====================

@app.route("/")
def index():
    """Render main application view."""
    return render_template("index.html")


@app.route("/api/categories", methods=["GET"])
@app.route("/api/proxy/news_categories_with_pages", methods=["GET"])
def get_categories():
    """Fetch indexed news categories and pages."""
    api_cfg = get_api_config()
    url = api_cfg["urls"]["news_categories_with_pages"]
    result = _call_backend_get(url)
    if not result.get("ok"):
        return jsonify({"status": False, "error": result.get("error")}), 502
    return jsonify({"status": True, "body": result.get("data")})


@app.route("/api/predefined-queries", methods=["GET"])
def get_predefined_queries():
    """Get random suggestions from predefined queries file."""
    count = request.args.get("count", default=3, type=int)
    count = max(1, min(10, count))
    queries = load_predefined_queries(count)
    return jsonify(queries)


@app.route("/api/search", methods=["POST"])
@app.route("/api/proxy/search_news", methods=["POST"])
def search_news():
    """Search news in categories matching user query."""
    api_cfg = get_api_config()
    url = api_cfg["urls"]["search_news"]

    # Support JSON or form payload
    if request.is_json:
        req_data = request.get_json(silent=True) or {}
        text_to_search = req_data.get("text_to_search") or req_data.get("query", "")
        num_of_results = req_data.get("num_of_results", 7)
        number_of_last_days = req_data.get("number_of_last_days") or req_data.get("last_days", 1)
        sites = req_data.get("sites", [])
        if isinstance(sites, list):
            sites_str = json.dumps(sites)
        else:
            sites_str = str(sites)

        form_data = {
            "text_to_search": text_to_search,
            "num_of_results": str(num_of_results),
            "number_of_last_days": str(number_of_last_days),
            "sites": sites_str,
        }
    else:
        form_data = request.form.to_dict()

    if not form_data.get("text_to_search"):
        return jsonify({"status": False, "error": "Brak zapytania (text_to_search)"}), 400

    result = _call_backend_post(url, form_data)
    if not result.get("ok"):
        return jsonify({"status": False, "error": result.get("error")}), 502
    return jsonify({"status": True, "body": result.get("data")})


@app.route("/api/generate", methods=["POST"])
@app.route("/api/proxy/generate_article", methods=["POST"])
def generate_article():
    """Generate article from search results using RAG model."""
    api_cfg = get_api_config()
    url = api_cfg["urls"]["generate_article"]

    if request.is_json:
        req_data = request.get_json(silent=True) or {}
        user_query = req_data.get("user_query") or req_data.get("query", "")
        news_ids = req_data.get("news_ids", [])
        article_type = req_data.get("article_type", "")
        sse_query_response_id = req_data.get("sse_query_response_id") or req_data.get("queryResponseId", 0)

        if isinstance(news_ids, list):
            news_ids_str = json.dumps(news_ids)
        else:
            news_ids_str = str(news_ids)

        form_data = {
            "user_query": user_query,
            "news_ids": news_ids_str,
            "article_type": article_type,
            "sse_query_response_id": str(sse_query_response_id),
        }
    else:
        form_data = request.form.to_dict()

    result = _call_backend_post(url, form_data, timeout=240)
    if not result.get("ok"):
        return jsonify({"status": False, "error": result.get("error")}), 502
    return jsonify({"status": True, "body": result.get("data")})


# ===================== Main =====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5101))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
