"use client";

import type { Source } from "@/types/research";

/** Citation anchors in the report link to these ids. */
export function sourceAnchor(id: string): string {
  return `source-${id}`;
}

export default function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="sources-heading" className="space-y-4 pt-4 border-t border-zinc-200/80">
      <div className="flex items-center justify-between">
        <h3 id="sources-heading" className="text-base font-semibold text-zinc-900">
          Sources & Citations{" "}
          <span className="ml-1 text-xs font-normal text-zinc-500">
            ({sources.length} verified {sources.length === 1 ? "page" : "pages"})
          </span>
        </h3>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {sources.map((source, index) => (
          <div
            key={source.id}
            id={sourceAnchor(source.id)}
            className="group flex flex-col justify-between rounded-xl border border-zinc-200/80 bg-white p-4 shadow-sm transition-all hover:border-zinc-300 hover:shadow-md"
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500">
                  <span className="flex h-5 w-5 items-center justify-center rounded-md bg-zinc-100 text-[10px] font-bold text-zinc-700 group-hover:bg-blue-50 group-hover:text-blue-700">
                    {index + 1}
                  </span>
                  <span className="truncate max-w-[150px]">{source.domain || "web"}</span>
                </span>

                <div className="flex items-center gap-1.5">
                  <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600">
                    {source.source_type}
                  </span>
                  {source.retrieval_method === "tavily_snippet" && (
                    <span
                      title="This page could not be scraped, so only the search snippet was available."
                      className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20"
                    >
                      Snippet
                    </span>
                  )}
                </div>
              </div>

              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2.5 block text-sm font-semibold text-zinc-900 transition hover:text-blue-600 line-clamp-2"
              >
                {source.title}
                <svg
                  className="ml-1 inline-block h-3.5 w-3.5 text-zinc-400 group-hover:text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>

              {source.snippet && (
                <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-zinc-500">
                  {source.snippet}
                </p>
              )}
            </div>

            <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-2 text-[11px] text-zinc-400">
              <span className="truncate max-w-[200px]">{source.url}</span>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-blue-600 hover:underline"
              >
                Visit page →
              </a>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
