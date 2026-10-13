import { readFile } from "node:fs/promises";
import path from "node:path";

/** How many suggestions are drawn on every page load / refresh. */
export const PREDEFINED_QUERIES_COUNT = 3;

const DEFAULT_FILE_NAME = "kreator-pytania.txt";

/**
 * Resolves the predefined-questions file.
 * Override with RADLAB_PREDEFINED_QUERIES_PATH (absolute or relative to cwd).
 */
export function predefinedQueriesFile(): string {
  const configured = process.env.RADLAB_PREDEFINED_QUERIES_PATH?.trim();
  const fileName = configured && configured.length ? configured : DEFAULT_FILE_NAME;
  return path.isAbsolute(fileName) ? fileName : path.resolve(process.cwd(), fileName);
}

/** Reads non-empty, de-duplicated lines of the questions file. */
export function parsePredefinedQueries(raw: string): string[] {
  const seen = new Set<string>();
  const queries: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const key = trimmed.toLocaleLowerCase("pl");
    if (seen.has(key)) continue;
    seen.add(key);
    queries.push(trimmed);
  }
  return queries;
}

/** Fisher-Yates shuffle, then take the requested number of entries. */
export function pickRandomQueries(queries: string[], count: number): string[] {
  const pool = [...queries];
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, Math.max(0, count));
}

/** Loads the file and draws a random subset of predefined queries. */
export async function drawPredefinedQueries(
  count: number = PREDEFINED_QUERIES_COUNT
): Promise<string[]> {
  const raw = await readFile(predefinedQueriesFile(), "utf-8");
  return pickRandomQueries(parsePredefinedQueries(raw), count);
}
