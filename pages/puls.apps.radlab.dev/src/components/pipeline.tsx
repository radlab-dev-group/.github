"use client";

import { t, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type PipelinePhase = "idle" | "searching" | "generating" | "done" | "error";

interface PipelineProps {
  lang: Lang;
  phase: PipelinePhase;
  stepLabel: string | null;
}

const STEP_KEYS = ["step_query", "step_search", "step_index", "step_gen"];

/**
 * A quiet progress strip that tells the reader where we are:
 * query -> search -> match -> generate.
 */
export function Pipeline({ lang, phase, stepLabel }: PipelineProps) {
  const activeIndex =
    phase === "idle" ? -1
    : phase === "searching" ? 1
    : phase === "generating" ? 3
    : phase === "done" ? 4
    : 0;

  return (
    <div className="paper-soft rounded-2xl px-5 py-4">
      <ol className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
        {STEP_KEYS.map((key, idx) => {
          const reached = activeIndex >= idx;
          const current =
            (idx === 1 && phase === "searching") ||
            (idx === 3 && phase === "generating") ||
            (idx === 2 && phase === "generating");
          return (
            <li key={key} className="flex min-w-0 items-center gap-2.5">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                  reached
                    ? "bg-accent-700 text-white"
                    : "bg-paper-300 text-ink-500",
                  current && "motion-safe:animate-blink"
                )}
              >
                {phase === "done" && reached ? "✓" : idx + 1}
              </div>
              <span
                className={cn(
                  "truncate text-sm transition-colors",
                  reached ? "font-medium text-ink-900" : "text-ink-400"
                )}
              >
                {t(lang, key)}
              </span>
            </li>
          );
        })}
      </ol>
      {stepLabel && (
        <div role="status" className="mt-3 border-t border-paper-300 pt-3 text-sm leading-relaxed text-accent-800">
          {stepLabel}
        </div>
      )}
    </div>
  );
}
