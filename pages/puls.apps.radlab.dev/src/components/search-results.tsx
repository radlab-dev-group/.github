"use client";

import { useMemo, useState } from "react";

import { t, type Lang } from "@/lib/i18n";
import { cn, formatCrawledDate, hostOf } from "@/lib/utils";
import type { NewsItem, SearchInCategory } from "@/lib/types";
import { PolarityBar, polarityMeta } from "./polarity-chart";

interface SearchResultsProps {
  lang: Lang;
  searchInCategory: SearchInCategory;
  categoriesSorted: string[];
}

type ViewMode = "wire" | "list";

interface SourceRow {
  citation: number;
  category: string;
  item: NewsItem;
}

/**
 * "Materiał źródłowy" — the evidence the article was built from.
 * Port of add_search_results_to_container / show_result_urls, restyled as a
 * numbered citation wire (horizontal scroll) with a compact list alternative.
 */
export function SearchResults({
  lang,
  searchInCategory,
  categoriesSorted,
}: SearchResultsProps) {
  const [view, setView] = useState<ViewMode>("wire");
  const [category, setCategory] = useState<string>("__all__");

  const orderedCategories = useMemo(() => {
    const present = Object.keys(searchInCategory).filter(
      (cat) => (searchInCategory[cat]?.length ?? 0) > 0
    );
    const known = categoriesSorted.filter((cat) => present.includes(cat));
    const extra = present.filter((cat) => !categoriesSorted.includes(cat));
    return [...known, ...extra.sort((a, b) => a.localeCompare(b))];
  }, [searchInCategory, categoriesSorted]);

  // Flat, citation-numbered list across every category.
  const allRows = useMemo<SourceRow[]>(() => {
    const rows: SourceRow[] = [];
    let citation = 1;
    for (const cat of orderedCategories) {
      for (const item of searchInCategory[cat] ?? []) {
        rows.push({ citation: citation++, category: cat, item });
      }
    }
    return rows.sort((a, b) =>
      (b.item.news_sub_page?.when_crawled ?? "").localeCompare(
        a.item.news_sub_page?.when_crawled ?? ""
      )
    );
  }, [orderedCategories, searchInCategory]);

  const rows = useMemo(
    () =>
      category === "__all__"
        ? allRows
        : allRows.filter((row) => row.category === category),
    [allRows, category]
  );

  if (!orderedCategories.length) return null;

  return (
    <section id="sources" className="paper animate-fade-up scroll-mt-24 rounded-3xl px-5 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-editorial text-2xl font-semibold tracking-tight text-ink-950">
              {t(lang, "material_title")}
            </h3>
            <span className="rounded-full bg-paper-200 px-2.5 py-0.5 text-xs font-medium text-ink-500">
              {allRows.length}
            </span>
          </div>
          <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-500">
            {t(lang, "material_hint")}
          </p>
        </div>

        <div className="flex items-center gap-1 self-start rounded-full border border-paper-300 bg-paper-200 p-1">
          {(["wire", "list"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setView(mode)}
              aria-pressed={view === mode}
              className={cn(
                "rounded-full px-3.5 py-1.5 text-sm transition",
                view === mode
                  ? "bg-paper-50 font-medium text-accent-800 shadow-sm"
                  : "text-ink-500 hover:text-ink-950"
              )}
            >
              {mode === "wire" ? `⇢ ${t(lang, "view_wire")}` : `≡ ${t(lang, "view_list")}`}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-5 border-t border-paper-300 pt-6 lg:flex-row lg:items-start">
        <PolarityBar lang={lang} items={allRows.map((row) => row.item)} />

        <div className="flex flex-wrap gap-1.5 lg:ml-auto lg:max-w-[60%] lg:justify-end">
          <FilterChip
            label={t(lang, "all_categories")}
            count={allRows.length}
            active={category === "__all__"}
            onClick={() => setCategory("__all__")}
          />
          {orderedCategories.map((cat) => (
            <FilterChip
              key={cat}
              label={cat}
              count={searchInCategory[cat].length}
              active={category === cat}
              onClick={() => setCategory(cat)}
            />
          ))}
        </div>
      </div>

      {view === "wire" ? (
        <div className="scroll-wire -mx-2 mt-6 flex snap-x snap-mandatory gap-3 overflow-x-auto px-2 pb-3">
          {rows.map((row) => (
            <WireCard key={row.citation} lang={lang} row={row} />
          ))}
        </div>
      ) : (
        <div className="mt-6 divide-y divide-paper-300 overflow-hidden rounded-2xl border border-paper-300">
          {rows.map((row) => (
            <ListRow key={row.citation} lang={lang} row={row} />
          ))}
        </div>
      )}
    </section>
  );
}

function FilterChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-full border px-3 py-1.5 text-[13px] transition",
        active
          ? "border-accent-600 bg-accent-50 text-accent-800"
          : "border-paper-300 bg-paper-50 text-ink-500 hover:border-accent-200 hover:text-accent-800"
      )}
    >
      {label}
      <span className="ml-1.5 text-xs opacity-70">{count}</span>
    </button>
  );
}

function WireCard({ lang, row }: { lang: Lang; row: SourceRow }) {
  const url = row.item.news_sub_page?.news_url ?? "";
  const date = formatCrawledDate(row.item.news_sub_page?.when_crawled ?? "");
  const meta = polarityMeta(row.item.polarity_3c);
  const excerpt = (row.item.generated_text ?? "").replace(/\s+/g, " ");

  return (
    <article className="group flex w-[300px] shrink-0 snap-start flex-col rounded-2xl border border-paper-300 bg-paper-50 p-5 transition hover:-translate-y-0.5 hover:border-accent-200 hover:shadow-md">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-paper-200 text-[11px] font-semibold text-ink-700">
          {row.citation}
        </span>
        <span className="truncate text-xs font-medium text-ink-700">
          {hostOf(url)}
        </span>
        <span
          className={cn("ml-auto h-2 w-2 shrink-0 rounded-full", meta.dot)}
          title={t(lang, meta.key)}
          role="img"
          aria-label={t(lang, meta.key)}
        />
      </div>

      <p className="line-clamp-5 font-editorial text-[15px] leading-relaxed text-ink-700">
        {excerpt}
      </p>

      <div className="mt-auto flex items-center justify-between gap-2 pt-4">
        <span className="text-xs text-ink-400">{date}</span>
        <a
          href={url}
          target="_blank"
          rel="noreferrer noopener"
          className="shrink-0 text-xs font-medium text-accent-700 underline-offset-4 transition hover:text-accent-800 hover:underline"
        >
          {t(lang, "open_source")} ↗
        </a>
      </div>
    </article>
  );
}

function ListRow({ lang, row }: { lang: Lang; row: SourceRow }) {
  const url = row.item.news_sub_page?.news_url ?? "";
  const date = formatCrawledDate(row.item.news_sub_page?.when_crawled ?? "");
  const meta = polarityMeta(row.item.polarity_3c);
  const excerpt = (row.item.generated_text ?? "").replace(/\s+/g, " ");

  return (
    <article className="group flex items-start gap-4 bg-paper-50 px-4 py-4 transition hover:bg-paper-200/60 sm:px-5">
      <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-paper-200 text-[11px] font-semibold text-ink-700">
        {row.citation}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 text-xs text-ink-400">
          <span className="font-medium text-ink-700">{hostOf(url)}</span>
          <span aria-hidden="true">·</span>
          <span>{date}</span>
          <span aria-hidden="true">·</span>
          <span className={meta.color}>{t(lang, meta.key)}</span>
        </div>
        <p className="mt-1.5 line-clamp-2 font-editorial text-[15px] leading-relaxed text-ink-700">
          {excerpt}
        </p>
      </div>
      <a
        href={url}
        target="_blank"
        rel="noreferrer noopener"
        aria-label={`${t(lang, "open_source")}: ${hostOf(url)}`}
        className="shrink-0 rounded-full border border-paper-300 px-3 py-1.5 text-sm text-accent-700 transition hover:border-accent-200 hover:bg-accent-50 hover:text-accent-800"
      >
        ↗
      </a>
    </article>
  );
}
