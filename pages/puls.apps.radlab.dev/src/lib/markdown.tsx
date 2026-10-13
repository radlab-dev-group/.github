import type { ReactNode } from "react";

/**
 * Minimal, dependency-free Markdown renderer for the generated article.
 *
 * The backend returns light Markdown (headings, bold, bullets). Rendering it
 * as React nodes (never dangerouslySetInnerHTML) keeps the bundle tiny and
 * avoids any XSS surface.
 */

const INLINE = /(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)/g;

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = new RegExp(INLINE.source, "g");
  let last = 0;
  let index = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    const key = `${keyPrefix}-${index++}`;

    if (token.startsWith("**")) {
      nodes.push(
        <strong key={key} className="font-semibold text-ink-950">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("`")) {
      nodes.push(
        <code
          key={key}
          className="rounded bg-paper-200 px-1 py-0.5 font-mono text-[0.85em] text-accent-800"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else {
      nodes.push(
        <em key={key} className="italic">
          {token.slice(1, -1)}
        </em>
      );
    }
    last = match.index + token.length;
  }

  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

/** Splits the first top-level heading so it can be used as the article title. */
export function splitHeadline(text: string): {
  headline: string | null;
  body: string;
} {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  for (let i = 0; i < Math.min(lines.length, 6); i++) {
    const match = /^#\s+(.+?)\s*$/.exec(lines[i]);
    if (match) {
      const body = lines
        .slice(0, i)
        .concat("", lines.slice(i + 1))
        .join("\n");
      return { headline: match[1], body };
    }
  }
  return { headline: null, body: text };
}

export function renderMarkdown(text: string): ReactNode[] {
  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");

  let paragraph: string[] = [];
  let list: string[] = [];
  let key = 0;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const content = paragraph.join(" ");
    blocks.push(
      <p key={`p-${key++}`} className="mb-6">
        {renderInline(content, `p-${key}`)}
      </p>
    );
    paragraph = [];
  };

  const flushList = () => {
    if (!list.length) return;
    const items = [...list];
    const ordered = items.every((item) => /^\d+[.)]\s+/.test(item));
    blocks.push(
      <ul
        key={`l-${key++}`}
        className="mb-7 space-y-3 border-l-2 border-accent-200 pl-5"
      >
        {items.map((item, idx) => (
          <li key={`li-${idx}`} className="flex gap-3">
            <span className="mt-[0.35em] shrink-0 font-sans text-sm font-semibold text-accent-700">
              {ordered ? `${idx + 1}.` : "•"}
            </span>
            <span className="min-w-0 flex-1">
              {renderInline(item.replace(/^(\*|-|\d+[.)])\s+/, ""), `li-${idx}`)}
            </span>
          </li>
        ))}
      </ul>
    );
    list = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      flushParagraph();
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) {
      flushList();
      flushParagraph();
      blocks.push(
        <div key={`hr-${key++}`} className="my-10 flex justify-center gap-3 text-accent-600" aria-hidden="true">
          <span>✧</span>
          <span>✧</span>
          <span>✧</span>
        </div>
      );
      continue;
    }

    const heading = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
    if (heading) {
      flushList();
      flushParagraph();
      const level = heading[1].length;
      const content = renderInline(heading[2], `h-${key}`);
      if (level <= 2) {
        blocks.push(
          <h3
            key={`h-${key++}`}
            className="mb-4 mt-12 text-[1.75rem] font-semibold leading-snug tracking-tight text-ink-950 sm:text-3xl"
          >
            {content}
          </h3>
        );
      } else {
        blocks.push(
          <h4
            key={`h-${key++}`}
            className="mb-3 mt-9 text-xl font-semibold leading-snug text-ink-950 sm:text-2xl"
          >
            {content}
          </h4>
        );
      }
      continue;
    }

    if (/^(\*|-|\d+[.)])\s+/.test(line)) {
      flushParagraph();
      list.push(line);
      continue;
    }

    paragraph.push(line);
  }

  flushList();
  flushParagraph();
  return blocks;
}
