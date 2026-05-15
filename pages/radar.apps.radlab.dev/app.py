"""
Radar Informacji — Przeglądarka informacji
Flask application that serves as a bridge to the external news aggregation API.

Komunikacja z backendem RADLAB jest zgodna z implementacją z official/
— używa `data=` (form-encoded body) w GET, a nie `params=` (query string).
Odpowiedź backendu ma strukturę:
    {"status": true, "body": {"summaries": [...], ...}}
"""

import json
import os
import urllib
import datetime
import requests

from flask import (
    Flask,
    render_template,
    jsonify,
    abort,
    request,
)


# ===================== App & Config =====================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

app = Flask(__name__, template_folder="templates", static_folder="static")


def load_config(path: str | None = None) -> dict:
    """Load the API configuration JSON."""
    cfg_path = path or CONFIG_PATH
    with open(cfg_path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def build_api_config(path: str | None = None) -> dict:
    """Return a normalised api_config dict (host + endpoint + full_url)."""
    cfg = load_config(path)
    nb = cfg["news_browser"]
    host = nb["host"].rstrip("/")
    ep = nb["endpoint"].lstrip("/")
    full_url = f"{host}/{ep}"
    return {"host": host, "endpoint": ep, "url": full_url}


api_config = build_api_config()


# ===================== Helpers =====================


def _unwrap_response(raw: dict) -> dict:
    """Rozpakowanie odpowiedzi backendu: {status, body} -> body."""
    if not isinstance(raw, dict):
        return {"status": False, "response": str(raw)}
    if raw.get("status") is True:
        return raw.get("body", {})
    return raw


def _call_backend(form_data: dict | None = None) -> dict:
    """GET do backendu z body form-encoded (ZGODNIE Z OFFICIAL)."""
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.get(
        api_config["url"],
        params=None,
        data=form_data,
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    return _unwrap_response(resp.json())


def _parse_date(date_str: str) -> datetime.date | None:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _compute_daily_stats(summaries: list) -> dict:
    """Oblicz statystyki dnia na podstawie wszystkich podsumowań."""
    total_articles = 0
    total_clusters = 0
    polarity_overall = {"positive": 0, "negative": 0, "ambivalent": 0}
    lang_overall = {}
    source_overall = {}
    source_domains_overall = set()
    pli_values = []

    for summary in summaries:
        for cluster in summary.get("clusters", []):
            stats = cluster.get("stats", {})
            n = stats.get("num_of_texts", 0)
            total_articles += n
            total_clusters += 1

            for k, v in stats.get("polarity_3c", {}).items():
                if k in polarity_overall:
                    polarity_overall[k] += v

            for lang, count in stats.get("language", {}).items():
                lang_overall[lang] = lang_overall.get(lang, 0) + count

            for src, count in stats.get("source", {}).items():
                source_overall[src] = source_overall.get(src, 0) + count
                try:
                    source_domains_overall.add(urllib.parse.urlparse(src).hostname)
                except Exception:
                    pass

            if "pli_value" in stats:
                pli_values.append(stats["pli_value"])

    avg_pli = sum(pli_values) / len(pli_values) if pli_values else 0

    # Clustering info
    clustering_info = {}
    if summaries and summaries[0].get("info"):
        cl = summaries[0]["info"].get("clustering", {})
        clustering_info = {
            "method": cl.get("clustering_method", "—"),
            "reducer": cl.get("reducer_method", "—"),
            "optimizer": cl.get("reducer_optimizer", "—"),
            "label_model": cl.get("genai_labels_model", "—"),
            "article_model": cl.get("genai_article_model", "—"),
        }

    # Top sources
    top_sources = sorted(source_overall.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    return {
        "total_articles": total_articles,
        "total_clusters": total_clusters,
        "total_summaries": len(summaries),
        "polarity": polarity_overall,
        "languages": lang_overall,
        "top_sources": top_sources,
        "unique_domains": len(source_domains_overall),
        "avg_polarity_index": round(avg_pli, 3),
        "clustering": clustering_info,
        "available_dates": {
            "today": today.isoformat(),
            "yesterday": yesterday.isoformat(),
        },
    }


# ===================== API Routes =====================


@app.route("/api/status")
def api_status():
    """Health-check / info endpoint."""
    return jsonify(
        {
            "service": "radar-informacji",
            "version": "1.0.0",
            "api_host": api_config["host"],
            "api_endpoint": api_config["endpoint"],
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )


@app.route("/api/dates")
def api_dates():
    """Zwraca dostępne daty z podsumowaniami."""
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    dates = []
    for d in [yesterday, today]:
        try:
            result = _call_backend(form_data={"date": d.isoformat()})
            if result and result.get("summaries"):
                dates.append(d.isoformat())
        except Exception:
            pass
    return jsonify({"dates": sorted(dates)})


@app.route("/api/summary")
def api_summary():
    """
    Pobierz podsumowanie dnia.

    Frontend -> Flask: GET /api/summary?date=YYYY-MM-DD
    Flask -> Backend:  GET {host}/{ep} z data={"date": ...} (form body)
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Brak parametru 'date'"}), 400

    d = _parse_date(date_str)
    if d is None:
        return (
            jsonify({"error": "Błędny format daty. Użyj YYYY-MM-DD lub DD.MM.YY."}),
            400,
        )

    try:
        raw_result = _call_backend(form_data={"date": d.isoformat()})
    except requests.RequestException as exc:
        return jsonify({"error": f"Błąd połączenia z API: {exc}"}), 502

    summaries = raw_result.get("summaries", []) if raw_result else []
    if not summaries:
        return jsonify(
            {
                "date": d.isoformat(),
                "summaries": [],
                "stats": None,
                "message": "Brak podsumowań dla tej daty.",
            }
        )

    stats = _compute_daily_stats(summaries)

    return jsonify(
        {
            "date": d.isoformat(),
            "summaries": summaries,
            "stats": stats,
        }
    )


# ===================== Page Routes =====================


@app.route("/")
def index():
    """Główna strona — wybór daty."""
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    return render_template(
        "index.html",
        today=today.isoformat(),
        yesterday=yesterday.isoformat(),
        api_host=api_config["host"],
    )


@app.route("/date/<date_str>")
def show_date(date_str):
    """Strona dedykowana dla konkretnej daty."""
    d = _parse_date(date_str)
    if d is None:
        abort(404, description="Błędny format daty.")
    return render_template(
        "date.html",
        date_str=date_str,
        date_obj=d,
        api_host=api_config["host"],
    )


@app.route("/algorithm")
def algorithm():
    """Podstrona z opisem algorytmu generowania podsumowań."""
    return render_template("algorithm.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5100))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
