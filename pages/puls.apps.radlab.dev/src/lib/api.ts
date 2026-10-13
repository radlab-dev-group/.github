import type {
  ArticleResponse,
  CategoriesWithPages,
  FilterPages,
  SearchInCategory,
  SearchResponse,
} from "./types";

/**
 * Client-side API layer for the News Creator.
 *
 * Every call is routed through the local Next.js proxy (/api/proxy/...) which
 * forwards to the radlab backend. This keeps the backend host on the server,
 * avoids browser CORS issues and mirrors exactly how the Streamlit UI
 * (src/api_public.py) talks to the backend.
 *
 * The request shapes (form-encoded POST bodies) are a 1:1 port of
 * PublicNewsStreamAPI.search_news_in_categories and
 * PublicNewsCreatorAPI.generate_article_from_search_result.
 */

export interface ApiResult<T> {
  ok: boolean;
  data: T | null;
  error?: string;
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * Unwraps a radlab response envelope.
 * Mirrors BasePublicApiInterface.return_response:
 *   - a dict with a "status" field -> return response["body"] when status is true
 *   - otherwise return the raw payload
 */
function unwrap<T>(payload: unknown): { ok: boolean; data: T | null; error?: string } {
  if (payload === null || payload === undefined) {
    return { ok: false, data: null, error: "Empty response" };
  }

  if (typeof payload === "object") {
    const record = payload as Record<string, unknown>;

    if (typeof record.status === "boolean") {
      if (record.status) {
        return { ok: true, data: record.body as T };
      }
      return { ok: false, data: null, error: "Backend reported an error." };
    }

    // No envelope -> assume the body itself.
    return { ok: true, data: payload as T };
  }

  // Non-object payload (string / number) -> treat as an error message.
  return { ok: false, data: null, error: String(payload) };
}

/**
 * GET categories together with their indexed pages.
 * Port of PublicNewsStreamAPI.list_available_categories_with_pages.
 */
export async function fetchCategoriesWithPages(): Promise<
  ApiResult<CategoriesWithPages>
> {
  try {
    const response = await fetch(
      "/api/proxy/news_categories_with_pages",
      { cache: "no-store" }
    );
    const payload = await parseBody(response);
    if (!response.ok) {
      return { ok: false, data: null, error: `HTTP ${response.status}` };
    }
    return unwrap<CategoriesWithPages>(payload);
  } catch (err) {
    return { ok: false, data: null, error: errMsg(err) };
  }
}

/**
 * Builds the filter_pages structure used by the creator.
 * Port of prepare_info_creator_public / add_category_and_pages_ui
 * (info_creator_window=True): every page of every category is active.
 */
export function buildFilterPages(
  categories: CategoriesWithPages
): FilterPages {
  const filterPages: FilterPages = {};
  for (const [category, info] of Object.entries(categories)) {
    filterPages[category] = (info.category_pages ?? []).map((page) => ({
      [page.main_url]: true,
    }));
  }
  return filterPages;
}

/**
 * Extracts the active site URLs from filter_pages.
 * Port of PublicNewsStreamAPI.search_news_in_categories (sites_urls loop).
 */
export function extractSites(filterPages: FilterPages): string[] {
  const sites: string[] = [];
  for (const pages of Object.values(filterPages)) {
    for (const pageMap of pages) {
      for (const [url, active] of Object.entries(pageMap)) {
        if (active) sites.push(url);
      }
    }
  }
  return sites;
}

/**
 * num_of_results derivation (port of call_search_api_and_show_result):
 *   num_of_results 0 -> last_days == 1 ? 7 : last_days < 7 ? 9 : 12
 */
export function deriveNumOfResults(numOfResults: number, lastDays: number) {
  if (numOfResults !== 0) return numOfResults;
  if (lastDays === 1) return 7;
  if (lastDays < 7) return 9;
  return 12;
}

/**
 * Search the index for news matching a query.
 * Port of PublicNewsStreamAPI.search_news_in_categories.
 */
export async function searchNews(params: {
  query: string;
  filterPages: FilterPages;
  numOfResults: number;
  lastDays: number;
}): Promise<ApiResult<SearchResponse>> {
  const { query, filterPages, numOfResults, lastDays } = params;

  const body = new URLSearchParams({
    text_to_search: query,
    num_of_results: String(numOfResults),
    number_of_last_days: String(lastDays),
    sites: JSON.stringify(extractSites(filterPages)),
  });

  try {
    const response = await fetch("/api/proxy/search_news", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    const payload = await parseBody(response);
    if (!response.ok) {
      return { ok: false, data: null, error: `HTTP ${response.status}` };
    }
    return unwrap<SearchResponse>(payload);
  } catch (err) {
    return { ok: false, data: null, error: errMsg(err) };
  }
}

/**
 * Generate an article from the matched news.
 * Port of PublicNewsCreatorAPI.generate_article_from_search_result.
 *
 * Note: the Streamlit client posts to the news_stream host using the
 * news_creator endpoint name; the proxy reproduces that exact behaviour.
 */
export async function generateArticle(params: {
  userQuery: string;
  newsIds: number[];
  articleType: string;
  queryResponseId: number;
}): Promise<ApiResult<ArticleResponse>> {
  const { userQuery, newsIds, articleType, queryResponseId } = params;

  const body = new URLSearchParams({
    user_query: userQuery,
    news_ids: JSON.stringify(newsIds),
    article_type: articleType,
    sse_query_response_id: String(queryResponseId),
  });

  try {
    const response = await fetch("/api/proxy/generate_article", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    const payload = await parseBody(response);
    if (!response.ok) {
      return { ok: false, data: null, error: `HTTP ${response.status}` };
    }
    return unwrap<ArticleResponse>(payload);
  } catch (err) {
    return { ok: false, data: null, error: errMsg(err) };
  }
}

/** Collects every news_id across categories (port of call_generate_article_api_and_show_response). */
export function collectNewsIds(searchInCategory: SearchInCategory): number[] {
  const ids: number[] = [];
  for (const items of Object.values(searchInCategory)) {
    for (const item of items) {
      const id = item.id ?? item.news_id;
      if (typeof id === "number") ids.push(id);
    }
  }
  return ids;
}

function errMsg(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}
