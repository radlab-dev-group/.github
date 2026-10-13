/** Joins class names, skipping falsy values. */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

/** "2026-10-13T08:15:30.123" -> "2026-10-13 08:15" (port of when_crawled formatting). */
export function formatCrawledDate(whenCrawled: string): string {
  return whenCrawled.split(".")[0].replace("T", " ");
}

/** Pretty-print a timestamp value coming from the backend. */
export function formatWhen(value: string | number | undefined, fallback = "—"): string {
  if (value === undefined || value === null || value === "") return fallback;
  const s = String(value);
  return s.split(".")[0].replace("T", " ");
}

export function hostOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function wordCount(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).length;
}

export function readingMinutes(text: string): number {
  return Math.max(1, Math.round(wordCount(text) / 180));
}

/** Groups the search results by category, preserving a preferred order. */
export function groupByCategory<T extends Record<string, unknown>>(
  searchInCategory: Record<string, T[]>
): [string, T[]][] {
  return Object.entries(searchInCategory).sort(([a], [b]) =>
    a.localeCompare(b)
  );
}
