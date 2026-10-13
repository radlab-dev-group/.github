# Puls Informacji by RadLab — lightweight web front-end

A modern, lightweight **showcase** front-end that re-implements the **Kreator
Aktualności (News Creator)** feature of the Streamlit playground, with a
light editorial theme, readable article typography, and a responsive layout.

Built with **Next.js 15 (App Router) + React 19 + Tailwind CSS v4 + TypeScript**.
No charting library, no UI kit — charts and panels are pure CSS/SVG, so the
whole bundle stays very light.

## What it does (1:1 port of the Streamlit creator)

1. On load it fetches the indexed **categories + pages**
   (`GET api/public/news_categories_with_pages`). The creator activates **all**
   pages of **all** categories (same as `prepare_info_creator_public`).
2. The user writes a query — or picks one of the **3 predefined phrases**
   loaded from `kreator-pytania.txt` (a fresh random draw on every page entry /
   refresh, plus a "draw again" button) — then picks a style
   (**simple / formal**) and a look-back window (**1 / 2 / 7 days**).
3. **Search** — `POST api/public/search_news` (form-encoded) with:
   `text_to_search`, `num_of_results`, `number_of_last_days`,
   `sites` (JSON list of active site URLs).
   * `num_of_results` is derived exactly like the Streamlit code:
     `0 -> (last_days == 1 ? 7 : last_days < 7 ? 9 : 12)`.
   * Results are shown as per-category tabs + a **polarity-3c** distribution
     (re-implementation of the plotly bar chart).
4. **Generate** — `POST api/public/generate_article_from_search` (form-encoded)
   with `user_query`, `news_ids`, `article_type`, `sse_query_response_id`.
   The prompt is assembled exactly as in the Streamlit UI
   (`p1 + formal|simple suffix`).
5. The generated **article** is rendered with its technical metadata
   (`when_generated`, `generation_time`, `model_used_to_generate`,
   number of matched news) plus word/reading-time stats, copy and `.md` download.

All response handling mirrors `BasePublicApiInterface.return_response`
(unwrap the `{status, body}` envelope).

## Architecture

```
browser
  └─ /api/proxy/<route>      (Next.js route handler, server-side)
        └─ RADLAB_API_HOST/<endpoint>   (radlab backend, form-encoded)
```

A thin **server proxy** (`src/app/api/proxy/[...path]/route.ts`) forwards each
call to the backend. This:

* avoids browser **CORS** problems (the backend is an intranet service),
* keeps the backend host **only in server-side env config**,
* mirrors exactly how the Streamlit UI resolves host/endpoints from
  `streamlit_ui/resources/configs/ui-configuration.json`.

### Source map (Streamlit → this app)

| Streamlit                                                        | This app                                             |
|------------------------------------------------------------------|------------------------------------------------------|
| `api_public.PublicNewsStreamAPI.list_available_categories_with_pages` | `src/lib/api.ts` → `fetchCategoriesWithPages`   |
| `api_public.PublicNewsStreamAPI.search_news_in_categories`       | `src/lib/api.ts` → `searchNews` (+`extractSites`)    |
| `api_public.PublicNewsCreatorAPI.generate_article_from_search_result` | `src/lib/api.ts` → `generateArticle`         |
| `api_config.ApiJsonConfiguration`                                | `src/config/app-config.ts` (env-driven)              |
| `ui_utils_public.prepare_info_creator_public`                    | `src/lib/api.ts` → `buildFilterPages`                |
| `actual_creator.call_search_api_and_show_result` (num results)   | `src/lib/api.ts` → `deriveNumOfResults`              |
| `ui_utils_public_search.show_polarity_chart` (plotly)            | `src/components/polarity-chart.tsx` (pure CSS)       |
| `NewsStreamMockQuestions.PREDEFINED_QUESTIONS` (hardcoded list) | `kreator-pytania.txt` → `src/lib/predefined-queries.ts` |
| `actual_creator.add_technical_info_for_gen_full_article`         | `src/components/article-result.tsx`                  |
| `language.py` / `ui_lang_def.xlsx` (creator keys)                | `src/lib/i18n.ts`                                    |

## Run it

```bash
cd my-radlab-app
npm install
cp .env.example .env.local   # then edit RADLAB_API_HOST if needed
npm run dev                  # http://localhost:3000
```

Production build:

```bash
npm run build
npm start
```

### Predefined search phrases

`kreator-pytania.txt` holds one phrase per line (blank lines and duplicates are
ignored). On every page entry / refresh `GET /api/predefined-queries` reads the
file and returns **3 random phrases**, rendered as clickable suggestions below
the query box; clicking one fills the query field, and "Losuj kolejne" re-draws
without reloading the page.

Point `RADLAB_PREDEFINED_QUERIES_PATH` at another file (relative to the app root
or absolute) to override the source.

### Configuration (`.env.local`)

| Variable                     | Default                                  |
|------------------------------|------------------------------------------|
| `RADLAB_API_HOST`            | `http://192.168.100.79:8567`              |
| `RADLAB_EP_NEWS_CATEGORIES`  | `api/public/news_categories_with_pages`   |
| `RADLAB_EP_SEARCH_NEWS`      | `api/public/search_news`                  |
| `RADLAB_EP_GENERATE_ARTICLE` | `api/public/generate_article_from_search` |
| `RADLAB_PREDEFINED_QUERIES_PATH` | `kreator-pytania.txt` |

Defaults match `streamlit_ui/resources/configs/ui-configuration.json`, so the
app works out of the box on the radlab network.
