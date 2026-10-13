"use client";

import { t, type Lang } from "@/lib/i18n";

/**
 * Placeholder shown in the (top) article slot while the model is working,
 * so the reader keeps the final deliverable in place instead of waiting on
 * an empty page.
 */
export function ArticleSkeleton({ lang, label }: { lang: Lang; label: string }) {
  return (
    <section aria-busy="true" className="paper relative overflow-hidden rounded-3xl">
      <div
        aria-hidden="true"
        className="h-1.5 w-full bg-gradient-to-r from-accent-700 via-accent-600 to-sun-200 opacity-60"
      />
      <div className="mx-auto max-w-[72ch] px-5 pb-10 pt-8 sm:px-10 sm:pt-12">
        <div className="mb-6 text-xs font-semibold uppercase tracking-[0.14em] text-accent-700/70">
          {t(lang, "article_onair")}
        </div>

        <div aria-hidden="true" className="mb-3 h-10 w-4/5 rounded-lg bg-paper-300 motion-safe:animate-pulse" />
        <div aria-hidden="true" className="mb-8 h-10 w-1/2 rounded-lg bg-paper-200 motion-safe:animate-pulse" />

        <div aria-hidden="true" className="mb-8 h-px w-full bg-paper-300" />

        <div aria-hidden="true" className="space-y-4">
          {[100, 96, 88, 92, 72, 90, 60].map((width, idx) => (
            <div
              key={idx}
              className="h-3.5 rounded bg-paper-200 motion-safe:animate-pulse"
              style={{
                width: `${width}%`,
                animationDelay: `${idx * 120}ms`,
              }}
            />
          ))}
        </div>

        <div
          role="status"
          className="mt-10 flex items-start gap-3 rounded-2xl bg-accent-50 px-4 py-3 text-sm text-accent-800"
        >
          <span
            aria-hidden="true"
            className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-accent-600 motion-safe:animate-blink"
          />
          <span className="min-w-0 break-words leading-relaxed">{label}</span>
        </div>
      </div>
    </section>
  );
}
