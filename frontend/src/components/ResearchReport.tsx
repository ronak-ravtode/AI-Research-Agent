"use client";

import { Children, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";

import { sourceAnchor } from "./SourceList";
import type { Source } from "@/types/research";

// Match ASCII and fullwidth citation brackets
const CITATION = /[【［〔]\s*(\d{1,3})\s*[】］〕]/g;

export default function ResearchReport({
  title,
  markdown,
  sources,
}: {
  title: string;
  markdown: string;
  sources: Source[];
}) {
  const [copied, setCopied] = useState(false);

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied; the answer is on screen regardless.
    }
  }

  return (
    <article aria-labelledby="report-heading" className="space-y-5">
      {/* Report Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-zinc-500 mb-1">
            <span className="flex h-4 w-4 items-center justify-center rounded bg-blue-100 text-[10px] text-blue-700">
              AI
            </span>
            <span>Synthesized Research Report · {sources.length} sources</span>
          </div>
          <h2 id="report-heading" className="text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl">
            {title}
          </h2>
        </div>

        <button
          type="button"
          onClick={copyAnswer}
          className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 shadow-sm transition hover:border-zinc-400 hover:bg-zinc-50 active:scale-95"
        >
          {copied ? (
            <>
              <svg className="h-3.5 w-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-emerald-700">Copied!</span>
            </>
          ) : (
            <>
              <svg className="h-3.5 w-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>Copy answer</span>
            </>
          )}
        </button>
      </div>

      {/* Honest Caveat Banner */}
      <div className="flex items-start gap-2.5 rounded-xl border border-zinc-200/90 bg-zinc-50/70 p-3.5 text-xs leading-relaxed text-zinc-600">
        <svg className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p>
          Citations link directly to retrieved sources. They make claims easy to inspect and
          verify, but do not replace independent critical judgment.
        </p>
      </div>

      {/* Markdown Body */}
      <div className="prose-paper pt-2">
        <ReactMarkdown
          components={{
            p: ({ children }) => <p>{linkifyCitations(children, sources)}</p>,
            li: ({ children }) => <li>{linkifyCitations(children, sources)}</li>,
            td: ({ children }) => <td>{linkifyCitations(children, sources)}</td>,
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </article>
  );
}

/**
 * Replace `[n]` in text nodes with a clickable badge linking to the matching source card.
 */
function linkifyCitations(children: ReactNode, sources: Source[]): ReactNode {
  return Children.map(children, (child) => {
    if (typeof child !== "string") return child;

    const parts = child.split(CITATION);
    if (parts.length === 1) return child;

    return parts.map((part, index) => {
      if (index % 2 === 0) return part;

      const number = Number(part);
      const source = sources[number - 1];
      if (!source) return "";

      return (
        <a
          key={`${number}-${index}`}
          href={`#${sourceAnchor(source.id)}`}
          onClick={(event) => {
            event.preventDefault();
            const el = document.getElementById(sourceAnchor(source.id));
            el?.scrollIntoView({ behavior: "smooth", block: "center" });
          }}
          title={source.title}
          className="mx-0.5 inline-flex items-center justify-center rounded-md bg-blue-50 px-1.5 py-0.5 align-baseline text-[11px] font-semibold text-blue-700 ring-1 ring-inset ring-blue-700/20 no-underline transition hover:bg-blue-600 hover:text-white hover:ring-transparent"
        >
          [{number}]
        </a>
      );
    });
  });
}
