"use client";

import { useMemo, useState } from "react";

import { t, type Lang } from "@/lib/i18n";
import { renderMarkdown, splitHeadline } from "@/lib/markdown";
import { formatWhen, readingMinutes, wordCount } from "@/lib/utils";
import type { ArticleResponse } from "@/lib/types";

interface ArticleResultProps {
  lang: Lang;
  article: ArticleResponse;
  numberOfNewsUsed: number;
  query: string;
}

/**
 * The generated article, presented as a magazine-style reading sheet.
 * Port of call_generate_article_api_and_show_response +
 * add_technical_info_for_gen_full_article, with the Markdown title promoted to
 * a real headline and the technical metadata tucked away in a disclosure.
 */
export function ArticleResult({
  lang,
  article,
  numberOfNewsUsed,
  query,
}: ArticleResultProps) {
  const [copied, setCopied] = useState(false);

  const text = article.article_str ?? article.article ?? article.new_article ?? "";

  const parsed = useMemo(() => splitHeadline(text), [text]);
  const blocks = useMemo(() => renderMarkdown(parsed.body), [parsed.body]);

  const stats = useMemo(
    () => ({
      words: wordCount(text),
      minutes: readingMinutes(text),
      when: formatWhen(article.when_generated),
      time:
        article.generation_time !== undefined
          ? String(article.generation_time)
          : "—",
      model: article.model_used_to_generate ?? "—",
    }),
    [article, text]
  );

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  }

  function handleDownload() {
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `radlab-article-${Date.now()}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const actions = (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={handleCopy}
        className="rounded-full border border-paper-300 bg-paper-50 px-4 py-2 text-xs font-medium text-ink-700 transition hover:border-accent-200 hover:bg-accent-50 hover:text-accent-800"
      >
        {copied ? `✓ ${t(lang, "copied")}` : `⧉ ${t(lang, "copy")}`}
      </button>
      <button
        onClick={handleDownload}
        className="rounded-full border border-paper-300 bg-paper-50 px-4 py-2 text-xs font-medium text-ink-700 transition hover:border-accent-200 hover:bg-accent-50 hover:text-accent-800"
      >
        ↓ {t(lang, "download")}
      </button>
    </div>
  );

  return (
    <section
      id="article"
      className="paper animate-fade-up relative overflow-hidden rounded-3xl"
    >
      {/* Thin accent ribbon at the very top of the sheet. */}
      <div
        aria-hidden="true"
        className="h-1.5 w-full bg-gradient-to-r from-accent-700 via-accent-600 to-sun-200"
      />

      <div className="mx-auto max-w-[72ch] px-5 pb-10 pt-8 sm:px-10 sm:pb-14 sm:pt-12">
        <div className="mb-6 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs font-semibold uppercase tracking-[0.14em] text-accent-700">
          <span>{t(lang, "article_onair")}</span>
        </div>

        {parsed.headline ? (
          <h2 className="mb-6 break-words font-editorial text-4xl font-semibold leading-[1.12] tracking-tight text-ink-950 sm:text-[3.1rem]">
            {parsed.headline}
          </h2>
        ) : null}

        <div className="mb-10 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-paper-300 py-4 text-sm text-ink-500">
          <span className="font-medium text-ink-700">
            {t(lang, "reading_time_long").replace("{minutes}", String(stats.minutes))}
          </span>
          <span aria-hidden="true" className="text-paper-400">·</span>
          <span>
            {t(lang, "based_on")}{" "}
            <a href="#sources" className="font-medium text-accent-700 underline-offset-4 hover:underline">
              {numberOfNewsUsed} {t(lang, "sources_used")}
            </a>
          </span>
          <span aria-hidden="true" className="text-paper-400">·</span>
          <span>{stats.when}</span>
          <div className="ml-auto hidden sm:block">{actions}</div>
        </div>

        <article className="article-body">
          {blocks.length > 0 ? (
            blocks
          ) : (
            <p className="font-sans text-base text-ink-500">
              {text || t(lang, "article_empty")}
            </p>
          )}
        </article>

        <div className="mt-12 rounded-2xl bg-paper-200 px-5 py-4 sm:flex sm:items-center sm:justify-between sm:gap-6">
          <p className="text-sm text-ink-700">{t(lang, "article_actions_hint")}</p>
          <div className="mt-3 sm:mt-0">{actions}</div>
        </div>

        <details className="group mt-6 text-sm text-ink-500">
          <summary className="inline-flex items-center gap-2 rounded-full py-1 text-xs font-medium text-ink-400 transition hover:text-ink-700 [&::-webkit-details-marker]:hidden">
            <span aria-hidden="true" className="transition group-open:rotate-90">
              ▸
            </span>
            {t(lang, "tech_details")}
          </summary>
          <dl className="mt-3 grid gap-x-6 gap-y-2 border-t border-paper-300 pt-3 text-xs sm:grid-cols-2">
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "article_topic")}</dt>
              <dd className="break-words text-right text-ink-700 sm:text-left">{query}</dd>
            </div>
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "news_used")}</dt>
              <dd className="text-ink-700">{numberOfNewsUsed}</dd>
            </div>
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "gen_model")}</dt>
              <dd className="break-words text-right text-ink-700 sm:text-left">{stats.model}</dd>
            </div>
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "gen_time")}</dt>
              <dd className="text-ink-700">{stats.time}</dd>
            </div>
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "word_count")}</dt>
              <dd className="text-ink-700">{stats.words}</dd>
            </div>
            <div className="flex justify-between gap-4 sm:block">
              <dt className="text-ink-400">{t(lang, "when_generated")}</dt>
              <dd className="text-ink-700">{stats.when}</dd>
            </div>
          </dl>
        </details>
      </div>
    </section>
  );
}
