"use client";

import Image from "next/image";

import { LANGS, t, type Lang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface HeaderProps {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  indexReady: boolean;
}

export function Header({ lang, onLangChange, indexReady }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-paper-300/80 bg-paper-50/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-4 sm:px-6">
        <a href="#top" className="flex min-w-0 items-center gap-3 rounded-xl">
          <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-full ring-2 ring-paper-300">
            <Image
              src="/logo-circle.png"
              alt="RadLab"
              fill
              sizes="44px"
              className="object-cover"
            />
          </div>
          <div className="leading-tight">
            <h1 className="font-editorial text-xl font-semibold tracking-tight text-ink-950 sm:text-2xl">
              {t(lang, "app_title")}
            </h1>
            <p className="mt-0.5 text-xs text-ink-500 sm:text-sm">
              {t(lang, "app_tagline")}
            </p>
          </div>
        </a>

        <div className="ml-auto flex items-center gap-3">
          <div
            className={cn(
              "hidden items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium sm:flex",
              indexReady
                ? "bg-accent-50 text-accent-700"
                : "bg-sun-100 text-sun-700"
            )}
            role="status"
          >
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                indexReady ? "bg-accent-600" : "bg-sun-700 motion-safe:animate-blink"
              )}
            />
            {indexReady ? t(lang, "live_badge") : t(lang, "live_badge_wait")}
          </div>

          <div className="flex items-center rounded-full border border-paper-300 bg-paper-200 p-1">
            {LANGS.map((item) => (
              <button
                key={item.code}
                onClick={() => onLangChange(item.code)}
                aria-pressed={lang === item.code}
                className={cn(
                  "rounded-full px-3 py-1.5 text-xs font-medium transition",
                  lang === item.code
                    ? "bg-paper-50 text-accent-800 shadow-sm"
                    : "text-ink-500 hover:text-ink-900"
                )}
                title={item.label}
              >
                {item.flag} {item.code.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
