export interface CategoryPage {
  main_url: string;
  [key: string]: unknown;
}

export interface CategoryInfo {
  display_name?: string;
  [key: string]: unknown;
}

export interface CategoryWithPages {
  category_info: CategoryInfo;
  category_pages: CategoryPage[];
}

export type CategoriesWithPages = Record<string, CategoryWithPages>;

export interface NewsSubPage {
  news_url: string;
  when_crawled: string;
  [key: string]: unknown;
}

export interface NewsItem {
  news_sub_page: NewsSubPage;
  generated_text: string;
  polarity_3c: "positive" | "negative" | "ambivalent" | null;
  id?: number;
  news_id?: number;
  [key: string]: unknown;
}

export type SearchInCategory = Record<string, NewsItem[]>;

export interface SearchResponse {
  query_response_id: number;
  search_result: SearchInCategory;
}

export interface ArticleResponse {
  article_str?: string;
  article?: string;
  new_article?: string;
  when_generated?: string;
  generation_time?: string | number;
  model_used_to_generate?: string;
  [key: string]: unknown;
}

/** {category: [{main_url: true}...]} — the filter_pages shape sent to search. */
export type FilterPages = Record<string, Record<string, boolean>[]>;
