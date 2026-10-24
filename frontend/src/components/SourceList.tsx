"use client";

import Link from "next/link";

import type { Source } from "@/types/research";

/** Stable anchor for a source card, used by deep links. */
export function sourceAnchor(id: string): string {
  return `source-${id}`;
}

export default function SourceList({
  researchId,
  sources,
}: {
  researchId: string;
  sources: Source[];
}) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="sources-heading"
      className="space-y-4 border-t border-zinc-200/80 pt-4 dark:border-zinc-800"
    >
      <div className="flex items-center justify-between">
        <h3 id="sources-heading" className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
          Sources{" "}
          <span className="ml-1 text-xs font-normal text-zinc-500 dark:text-zinc-400">
            ({sources.length} retrieved {sources.length === 1 ? "page" : "pages"})
          </span>
        </h3>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {sources.map((source, index) => (
          <div
            key={source.id}
            id={sourceAnchor(source.id)}
            className="group flex flex-col justify-between rounded-xl border border-zinc-200/80 bg-white p-4 shadow-sm transition-all hover:border-zinc-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-600"
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                  <span className="flex h-5 w-5 items-center justify-center rounded-md bg-zinc-100 text-[10px] font-bold text-zinc-700 group-hover:bg-blue-50 group-hover:text-blue-700 dark:bg-zinc-800 dark:text-zinc-300 dark:group-hover:bg-blue-950 dark:group-hover:text-blue-300">
                    {index + 1}
                  </span>
                  <span className="max-w-[150px] truncate">{source.domain || "web"}</span>
                </span>

                <div className="flex items-center gap-1.5">
                  <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                    {source.source_type}
                  </span>
                  {source.retrieval_method === "tavily_snippet" && (
                    <span
                      title="This page could not be scraped, so only the search snippet was available."
                      className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-500/30"
                    >
                      Snippet
                    </span>
                  )}
                </div>
              </div>

              <Link
                href={`/r/${researchId}/sources/${source.id}`}
                className="mt-2.5 line-clamp-2 block text-sm font-semibold text-zinc-900 transition hover:text-blue-600 dark:text-zinc-100 dark:hover:text-blue-400"
              >
                {source.title}
              </Link>

              {source.snippet && (
                <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                  {source.snippet}
                </p>
              )}
            </div>

            <div className="mt-3 flex items-center justify-between gap-2 border-t border-zinc-100 pt-2 text-[11px] text-zinc-400 dark:border-zinc-800">
              <span className="max-w-[200px] truncate">{source.url}</span>
              <div className="flex shrink-0 items-center gap-2">
                <Link
                  href={`/r/${researchId}/sources/${source.id}`}
                  className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  Read
                </Link>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-zinc-500 hover:text-zinc-800 hover:underline dark:text-zinc-400 dark:hover:text-zinc-200"
                >
                  Original ↗
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
