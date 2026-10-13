"use client";

import { t, type Lang } from "@/lib/i18n";
import { hostOf } from "@/lib/utils";
import type { CategoriesWithPages } from "@/lib/types";

interface TickerProps {
  lang: Lang;
  categories?: CategoriesWithPages;
}

/** A compact, wrapping list of indexed sources. */
export function Ticker({ lang, categories }: TickerProps) {
  const seenUrls = new Set<string>();
  const items: string[] = [];
  if (categories) {
    for (const info of Object.values(categories)) {
      for (const page of info.category_pages ?? []) {
        if (seenUrls.has(page.main_url)) continue;
        seenUrls.add(page.main_url);
        items.push(hostOf(page.main_url));
      }
    }
  }

  const unique = items;
  const content = unique.length
    ? unique
    : [t(lang, "index_note")];

  const line = (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      {content.map((item, idx) => (
        <span
          key={`${item}-${idx}`}
          className="inline-flex max-w-full items-center gap-2 text-xs leading-relaxed text-slate-600 [overflow-wrap:anywhere]"
        >
          <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-teal-600" />
          {item}
        </span>
      ))}
    </div>
  );

  return (
    <div className="border-b border-slate-200 bg-white px-5 py-3 sm:px-8">
      {line}
    </div>
  );
}
