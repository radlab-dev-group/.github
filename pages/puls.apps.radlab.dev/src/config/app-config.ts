export interface AppConfig {
  host: string;
  endpoints: {
    newsCategoriesWithPages: string;
    searchNews: string;
    generateArticle: string;
  };
}

/**
 * Resolves the backend host + endpoints from environment variables.
 * Defaults mirror streamlit_ui/resources/configs/ui-configuration.json
 * so the app works out of the box in the radlab network.
 */
export function getAppConfig(): AppConfig {
  const rawHost =
    process.env.RADLAB_API_HOST ?? "http://192.168.100.79:8567";

  return {
    host: rawHost.trim().replace(/\/+$/, ""),
    endpoints: {
      newsCategoriesWithPages:
        process.env.RADLAB_EP_NEWS_CATEGORIES ??
        "api/public/news_categories_with_pages",
      searchNews:
        process.env.RADLAB_EP_SEARCH_NEWS ?? "api/public/search_news",
      generateArticle:
        process.env.RADLAB_EP_GENERATE_ARTICLE ??
        "api/public/generate_article_from_search",
    },
  };
}

export function buildUrl(path: string): string {
  const { host, endpoints } = getAppConfig();
  const ep = path
    .split("/")
    .map((seg) => encodeURIComponent(seg))
    .join("/");
  return `${host}/${ep}`;
}
