"use client";

import { Children, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";

import { sourceAnchor } from "./SourceList";
import type { Source } from "@/types/research";

const CITATION = /\[(\d{1,3})\]/g;

/** Short, honest caveat shown above every answer. */
export default function ResearchReport({
  title,
  markdown,
  sources,
}: {
  title: string;
  markdown: string;
  sources: Source[];
}) {
  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(markdown);
    } catch {
      // Clipboard access can be denied; the answer is on screen regardless.
    }
  }

  return (
    <section aria-labelledby="report-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 id="report-heading" className="text-xl font-semibold text-stone-900">
          {title}
        </h2>
        <button
          type="button"
          onClick={copyAnswer}
          className="shrink-0 rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 transition hover:border-stone-500 hover:bg-stone-50"
        >
          Copy answer
        </button>
      </div>

      <p className="rounded-md border border-stone-200 bg-stone-50 px-3 py-2 text-xs leading-relaxed text-stone-600">
        Citations link to the sources that were actually retrieved. They make the answer
        easier to check; they do not guarantee every claim is true.
      </p>

      <article className="prose-paper">
        <ReactMarkdown
          // Raw HTML is never enabled, so model output cannot inject markup.
          components={{
            p: ({ children }) => <p>{linkifyCitations(children, sources)}</p>,
            li: ({ children }) => <li>{linkifyCitations(children, sources)}</li>,
            td: ({ children }) => <td>{linkifyCitations(children, sources)}</td>,
          }}
        >
          {markdown}
        </ReactMarkdown>
      </article>
    </section>
  );
}

/**
 * Replace `[n]` in text nodes with a link to the matching source card.
 *
 * Walking rendered children rather than rewriting the Markdown means link syntax that is
 * already in the text (`[Title](url)`) is left completely alone.
 */
function linkifyCitations(children: ReactNode, sources: Source[]): ReactNode {
  return Children.map(children, (child) => {
    if (typeof child !== "string") return child;

    const parts = child.split(CITATION);
    if (parts.length === 1) return child;

    return parts.map((part, index) => {
      // With a capture group, split() alternates text, capture, text, capture...
      // Odd indices are the captured citation number itself.
      if (index % 2 === 0) return part;

      const number = Number(part);
      const source = sources[number - 1];
      if (!source) return "";

      return (
        <a
          key={`${number}-${index}`}
          href={`#${sourceAnchor(source.id)}`}
          onClick={(event) => {
            // Scroll the card into view and give it a brief highlight.
            event.preventDefault();
            document
              .getElementById(sourceAnchor(source.id))
              ?.scrollIntoView({ behavior: "smooth", block: "center" });
          }}
          title={source.title}
          className="mx-0.5 inline-flex min-w-[1.4rem] items-center justify-center rounded bg-stone-900 px-1 py-px align-baseline text-[0.7rem] font-semibold text-white no-underline hover:bg-stone-700"
        >
          {number}
        </a>
      );
    });
  });
}
