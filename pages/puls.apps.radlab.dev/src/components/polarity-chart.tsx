"use client";

import { t, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { NewsItem } from "@/lib/types";

export const POLARITY_ORDER = ["positive", "negative", "ambivalent"] as const;

const POLARITY_META: Record<
  string,
  { key: string; label: string; color: string; bar: string; dot: string }
> = {
  positive: {
    key: "pos",
    label: "●",
    color: "text-emerald-700",
    bar: "bg-emerald-600",
    dot: "bg-emerald-600",
  },
  negative: {
    key: "neg",
    label: "●",
    color: "text-rose-700",
    bar: "bg-rose-600",
    dot: "bg-rose-600",
  },
  ambivalent: {
    key: "amb",
    label: "●",
    color: "text-ink-500",
    bar: "bg-paper-400",
    dot: "bg-paper-400",
  },
};

export function polarityMeta(value: string | null | undefined) {
  if (value && POLARITY_META[value]) return POLARITY_META[value];
  return {
    key: "no_polarity",
    label: "●",
    color: "text-ink-400",
    bar: "bg-ink-400",
    dot: "bg-ink-400",
  };
}

export function countPolarity(items: NewsItem[]): Record<string, number> {
  const counts: Record<string, number> = {
    positive: 0,
    negative: 0,
    ambivalent: 0,
    unclassified: 0,
  };
  for (const item of items) {
    if (item.polarity_3c && counts[item.polarity_3c] !== undefined) {
      counts[item.polarity_3c] += 1;
    } else {
      counts.unclassified += 1;
    }
  }
  return counts;
}

/**
 * Lightweight re-implementation of the Streamlit plotly "polarity 3c" chart.
 * `stacked` renders a single one-line distribution bar used in panel headers.
 */
export function PolarityBar({
  lang,
  items,
  className,
}: {
  lang: Lang;
  items: NewsItem[];
  className?: string;
}) {
  const counts = countPolarity(items);
  const total = items.length;
  if (total < 1) return null;

  const segments = [
    ...POLARITY_ORDER.map((key) => ({ key, count: counts[key] })),
    { key: "unclassified", count: counts.unclassified },
  ].filter((segment) => segment.count > 0);

  return (
    <div className={cn("w-full min-w-0 lg:w-auto lg:min-w-[220px]", className)}>
      <div className="mb-2 flex items-center justify-between gap-3 text-xs text-ink-500">
        <span className="font-medium text-ink-700">{t(lang, "polarity_title")}</span>
        <span>{total}</span>
      </div>
      <div aria-hidden="true" className="flex h-2.5 w-full overflow-hidden rounded-full bg-paper-200">
        {segments.map(({ key, count }) => (
          <div
            key={key}
            className={cn("h-full", polarityMeta(key).bar)}
            style={{ width: `${(count / total) * 100}%` }}
            title={`${t(lang, polarityMeta(key).key)}: ${count}`}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1.5 text-xs">
        {segments.map(({ key, count }) => (
          <span key={key} className="flex items-center gap-1">
            <span
              aria-hidden="true"
              className={cn("h-1.5 w-1.5 rounded-full", polarityMeta(key).dot)}
            />
            <span className={polarityMeta(key).color}>
              {t(lang, polarityMeta(key).key)}
            </span>
            <span className="text-ink-400">
              {Math.round((count / total) * 100)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
