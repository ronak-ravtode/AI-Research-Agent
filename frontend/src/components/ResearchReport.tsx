"use client";

import Link from "next/link";
import { Children, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";

import type { Source } from "@/types/research";

// Match ASCII and fullwidth citation brackets
const CITATION = /[【［〔]\s*(\d{1,3})\s*[】］〕]/g;

export default function ResearchReport({
  researchId,
  title,
  markdown,
  sources,
  citationPreview = true,
}: {
  researchId: string;
  title: string;
  markdown: string;
  sources: Source[];
  citationPreview?: boolean;
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
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-200/80 pb-4 dark:border-zinc-800">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
            <span className="flex h-4 w-4 items-center justify-center rounded bg-blue-100 text-[10px] text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              AI
            </span>
            <span>
              Synthesized report · {sources.length}{" "}
              {sources.length === 1 ? "source" : "sources"}
            </span>
          </div>
          <h2
            id="report-heading"
            className="text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50"
          >
            {title}
          </h2>
        </div>

        <button
          type="button"
          onClick={copyAnswer}
          className="focus-ring inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-700 shadow-sm transition hover:border-zinc-400 hover:bg-zinc-50 active:scale-95 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:border-zinc-500 dark:hover:bg-zinc-800"
        >
          {copied ? (
            <>
              <svg className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-emerald-700 dark:text-emerald-400">Copied</span>
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

      <div className="flex items-start gap-2.5 rounded-xl border border-zinc-200/90 bg-zinc-50/70 p-3.5 text-xs leading-relaxed text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-400">
        <svg className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p>
          Citations link to the exact page that was read, where you can inspect the full
          extracted text. They make claims easy to check, but do not replace your own
          judgment.
        </p>
      </div>

      <div className="prose-paper pt-2">
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p>{linkifyCitations(children, sources, researchId, citationPreview)}</p>
            ),
            li: ({ children }) => (
              <li>{linkifyCitations(children, sources, researchId, citationPreview)}</li>
            ),
            td: ({ children }) => (
              <td>{linkifyCitations(children, sources, researchId, citationPreview)}</td>
            ),
            a: ({ href, children, ...props }) => {
              const isExternal = Boolean(href && /^https?:\/\//i.test(href));
              return (
                <a
                  href={href}
                  target={isExternal ? "_blank" : undefined}
                  rel={isExternal ? "noopener noreferrer" : undefined}
                  {...props}
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </article>
  );
}

/**
 * Replace `[n]` in text nodes with a clickable badge that opens the source reader,
 * with an optional hover/focus preview of the cited page.
 */
function linkifyCitations(
  children: ReactNode,
  sources: Source[],
  researchId: string,
  showPreview: boolean,
): ReactNode {
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
        <span key={`${number}-${index}`} className="group/cite relative inline-block">
          <Link
            href={`/r/${researchId}/sources/${source.id}`}
            aria-label={`Source ${number}: ${source.title}`}
            className="mx-0.5 inline-flex items-center justify-center rounded-md bg-blue-50 px-1.5 py-0.5 align-baseline text-[11px] font-semibold text-blue-700 no-underline ring-1 ring-inset ring-blue-700/20 transition hover:bg-blue-600 hover:text-white hover:ring-transparent dark:bg-blue-950/60 dark:text-blue-300 dark:ring-blue-500/30 dark:hover:bg-blue-600 dark:hover:text-white"
          >
            [{number}]
          </Link>

          {showPreview && (
            <span
              role="tooltip"
              className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 hidden w-64 -translate-x-1/2 rounded-xl border border-zinc-200 bg-white p-3 text-left shadow-xl group-hover/cite:block group-focus-within/cite:block dark:border-zinc-700 dark:bg-zinc-900"
            >
              <span className="block text-[11px] font-semibold leading-snug text-zinc-900 dark:text-zinc-100">
                {source.title}
              </span>
              <span className="mt-1 block text-[10px] text-zinc-500 dark:text-zinc-400">
                {source.domain || "web"} · {source.source_type}
              </span>
              {source.snippet && (
                <span className="mt-1.5 line-clamp-3 block text-[10.5px] leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {source.snippet}
                </span>
              )}
              <span className="mt-1.5 block text-[10px] font-medium text-blue-600 dark:text-blue-400">
                Open source →
              </span>
            </span>
          )}
        </span>
      );
    });
  });
}
