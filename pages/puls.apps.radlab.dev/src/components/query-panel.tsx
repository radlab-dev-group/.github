"use client";

import { useState } from "react";

import { t, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type ArticleStyle = "simple" | "formal";

interface QueryPanelProps {
  lang: Lang;
  query: string;
  onQueryChange: (value: string) => void;
  style: ArticleStyle;
  onStyleChange: (value: ArticleStyle) => void;
  lastDays: number;
  onLastDaysChange: (value: number) => void;
  onSubmit: () => void;
  busy: boolean;
  error: string | null;
  hasRun: boolean;
  /** Random predefined queries drawn on each page entry / refresh. */
  suggestions?: string[];
  onUseSuggestion?: (value: string) => void;
  onShuffleSuggestions?: () => void;
  /** When true the panel shrinks to a slim bar so the article owns the top. */
  collapsed?: boolean;
}

const LAST_DAYS_OPTIONS: { days: number; key: string }[] = [
  { days: 1, key: "day_1" },
  { days: 2, key: "day_2" },
  { days: 7, key: "day_7" },
];

const STYLE_OPTIONS: {
  value: ArticleStyle;
  icon: string;
  labelKey: string;
  descKey: string;
}[] = [
  { value: "simple", icon: "☕", labelKey: "style_simple", descKey: "style_simple_desc" },
  { value: "formal", icon: "🏛", labelKey: "style_formal", descKey: "style_formal_desc" },
];

export function QueryPanel({
  lang,
  query,
  onQueryChange,
  style,
  onStyleChange,
  lastDays,
  onLastDaysChange,
  onSubmit,
  busy,
  error,
  hasRun,
  suggestions = [],
  onUseSuggestion,
  onShuffleSuggestions,
  collapsed = false,
}: QueryPanelProps) {
  const [localError, setLocalError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  function handleSubmit() {
    if (!query.trim()) {
      setLocalError(t(lang, "no_query_error"));
      return;
    }
    setLocalError(null);
    setExpanded(false);
    onSubmit();
  }

  const shownError = localError ?? error;
  const compact = collapsed && !expanded;
  const daysLabel =
    LAST_DAYS_OPTIONS.find((option) => option.days === lastDays)?.key ?? null;

  if (compact) {
    return (
      <section className="paper rounded-2xl px-4 py-3 sm:px-5">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
              {t(lang, "article_topic")}
            </div>
            <button
              onClick={() => setExpanded(true)}
              className="block w-full truncate text-left font-editorial text-base text-ink-900 transition hover:text-accent-700"
              title={query}
            >
              {query}
            </button>
          </div>
          <span className="hidden shrink-0 rounded-full bg-paper-200 px-3 py-1 text-xs text-ink-500 sm:inline">
            {t(lang, style === "simple" ? "style_simple" : "style_formal")}
            {daysLabel ? ` · ${t(lang, daysLabel)}` : ""}
          </span>
          <button
            onClick={() => setExpanded(true)}
            className="shrink-0 rounded-full border border-paper-300 bg-paper-50 px-4 py-2 text-xs font-medium text-ink-700 transition hover:border-accent-200 hover:text-accent-800"
          >
            {t(lang, "btn_new_topic")}
          </button>
          <button
            onClick={handleSubmit}
            disabled={busy}
            className="shrink-0 rounded-full bg-accent-700 px-4 py-2 text-xs font-semibold text-white transition hover:bg-accent-800 disabled:opacity-60"
          >
            {busy ? "…" : t(lang, "btn_run_again")}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="paper relative overflow-hidden rounded-3xl p-5 sm:p-8">
      <div className="relative">
        <div className="mb-4 flex items-start gap-3">
          <h2
            id="query-heading"
            className="font-editorial text-2xl font-semibold tracking-tight text-ink-950"
          >
            {t(lang, "query_label")}
          </h2>
          {collapsed && (
            <button
              onClick={() => setExpanded(false)}
              className="ml-auto rounded-full border border-paper-300 px-3 py-1.5 text-xs text-ink-500 transition hover:text-ink-900"
            >
              {t(lang, "btn_close_editor")}
            </button>
          )}
        </div>

        <label className="block">
          <textarea
            aria-labelledby="query-heading"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") handleSubmit();
            }}
            placeholder={t(lang, "query_placeholder")}
            rows={3}
            disabled={busy}
            className="w-full resize-y rounded-2xl border border-paper-300 bg-paper-50 px-5 py-4 font-editorial text-lg leading-relaxed text-ink-950 shadow-inner placeholder:text-ink-400 transition focus:border-accent-600 focus:bg-white focus:outline-none disabled:opacity-60 sm:text-xl"
          />
        </label>

        {suggestions.length > 0 && (
          <div className="mt-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-ink-700">
                {t(lang, "suggestions_title")}
              </span>
              <span className="hidden text-sm text-ink-400 sm:inline">
                · {t(lang, "suggestions_hint")}
              </span>
              {onShuffleSuggestions && (
                <button
                  type="button"
                  onClick={onShuffleSuggestions}
                  className="ml-auto rounded-full px-3 py-1.5 text-xs font-medium text-accent-700 transition hover:bg-accent-50 hover:text-accent-800"
                >
                  ⟳ {t(lang, "suggestions_refresh")}
                </button>
              )}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={`${idx}-${suggestion}`}
                  type="button"
                  disabled={busy}
                  title={suggestion}
                  onClick={() => onUseSuggestion?.(suggestion)}
                  className={cn(
                    "max-w-full rounded-full border px-4 py-2 text-left text-sm leading-snug transition disabled:opacity-60",
                    query.trim() === suggestion.trim()
                      ? "border-accent-600 bg-accent-50 text-accent-800"
                      : "border-paper-300 bg-paper-50 text-ink-700 hover:border-accent-200 hover:bg-accent-50/60 hover:text-ink-950"
                  )}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-7 grid gap-6 border-t border-paper-300 pt-6 md:grid-cols-[1fr_auto]">
          <div>
            <span className="mb-2.5 block text-sm font-medium text-ink-700">
              {t(lang, "style_label")}
            </span>
            <div className="grid gap-2 sm:grid-cols-2">
              {STYLE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  disabled={busy}
                  onClick={() => onStyleChange(option.value)}
                  aria-pressed={style === option.value}
                  className={cn(
                    "flex items-start gap-3 rounded-2xl border px-4 py-3 text-left transition disabled:opacity-60",
                    style === option.value
                      ? "border-accent-600 bg-accent-50 text-accent-800"
                      : "border-paper-300 bg-paper-50 text-ink-700 hover:border-paper-400 hover:text-ink-950"
                  )}
                >
                  <span aria-hidden="true" className="mt-0.5 text-lg leading-none">
                    {option.icon}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">
                      {t(lang, option.labelKey)}
                    </span>
                    <span className="block text-xs text-ink-500">
                      {t(lang, option.descKey)}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="mb-2.5 block text-sm font-medium text-ink-700">
              {t(lang, "last_days_label")}
            </span>
            <div className="flex gap-1 rounded-full border border-paper-300 bg-paper-200 p-1">
              {LAST_DAYS_OPTIONS.map((option) => (
                <button
                  key={option.days}
                  type="button"
                  disabled={busy}
                  onClick={() => onLastDaysChange(option.days)}
                  aria-pressed={lastDays === option.days}
                  className={cn(
                    "min-w-16 rounded-full px-4 py-2 text-sm transition disabled:opacity-60",
                    lastDays === option.days
                      ? "bg-paper-50 font-semibold text-accent-800 shadow-sm"
                      : "text-ink-500 hover:text-ink-950"
                  )}
                >
                  {t(lang, option.key)}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={busy}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-full px-7 py-3.5 text-base font-semibold text-white shadow-md transition",
              "bg-accent-700 shadow-accent-700/20",
              "hover:-translate-y-px hover:bg-accent-800 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            )}
          >
            {busy ? "…" : hasRun ? t(lang, "btn_run_again") : t(lang, "btn_run")}
            {!busy && <span aria-hidden="true">→</span>}
          </button>
          <span className="text-xs text-ink-400">{t(lang, "shortcut_hint")}</span>
        </div>

        {shownError && (
          <div
            role="alert"
            className="mt-5 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <span aria-hidden="true">⚠</span>
            {shownError}
          </div>
        )}
      </div>
    </section>
  );
}
