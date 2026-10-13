**Radar Informacji**

A reader-friendly web application for browsing daily news summaries. Data is fetched from the RADLAB backend via an internal API.

The UI is a single-column "daily edition" layout designed for reading: a masthead with the date and a one-sentence
summary of the day, a mood bar (share of positive / neutral / negative coverage), a two-tier table of contents
(the few most-covered topics as a numbered list, the remaining ~30 as compact collapsible chips), and each topic
rendered as an article with comfortable typography. Sources (grouped by site), related days and technical details
are collapsed under each article so they don't distract from the text. Dark mode, bookmarks, search and a
sentiment filter are available.

## Structure

```
radar/
├── app.py              # Main Flask application (API + pages)
├── run.sh              # Startup script
├── requirements.txt    # Python dependencies
├── config/
│   └── config.json     # Backend API configuration
├── templates/
│   ├── base.html       # Base template (navigation, footer)
│   ├── index.html      # Home page (date selector)
│   ├── date.html       # Page dedicated to a specific date
│   └── algorithm.html  # Technical algorithm description
└── static/
    ├── css/
    │   └── style.css   # Reader-edition CSS (light + dark theme)
    └── js/
        └── app.js      # Front‑end logic (API calls, rendering)
```

## Running the Application

```shell script
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure the API (optional)
# Edit config/config.json – by default it points to:
#   host: http://192.168.100.79:8567
#   endpoint: api/public/articles_summary_of_day

# 3. Start the app
./run.sh

# Or run directly:
python3 -m flask --app app run --port 5100
```

## Configuration

In `config/config.json`:

```json
{
  "news_browser": {
    "host": "http://192.168.100.79:8567",
    "endpoint": "api/public/articles_summary_of_day"
  }
}
```

## Environment Variables

| Variable      | Default | Description                    |
|------|---------|----|
| `PORT`        | `5100`  | Flask server port              |
| `FLASK_DEBUG` | `0`     | Debug mode flag                |
| `CONFIG_PATH` | path    | Path to the configuration file |

## Page Routes

| Endpoint                        | Description                                 |
|------                            |----|
| `/`                             | Home page — date selector                  |
| `/date/YYYY-MM-DD`              | Page dedicated to a specific date          |
| `/algorithm`                    | Technical algorithm description            |

## Internal API

| Endpoint                           | Description                                 |
|------                               |----|
| `GET /api/status`                  | Service status                             |
| `GET /api/dates`                   | Available dates with summaries             |
| `GET /api/summary?date=YYYY-MM-DD` | Retrieve the news summary for a given date |

## RADLAB Backend

The application communicates with the RADLAB backend through the endpoint:

```
{host}/{endpoint}
```

with the query parameter `date` (ISO format).

The response contains a list of summaries (`summaries`), each consisting of:

- `info` – metadata (clustering method, generation date)
- `clusters` – list of topics, each with:
    - `label_str` – topic title
    - `article_text` – summary text
    - `stats` – statistics (number of articles, polarity)
    - `news_urls` – list of source URLs
    - `similarity` – similar days
