"use client";

import type { Source } from "@/types/research";

/** Citation anchors in the report link to these ids. */
export function sourceAnchor(id: string): string {
  return `source-${id}`;
}

export default function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-stone-500">No sources were retrieved.</p>;
  }

  return (
    <section aria-labelledby="sources-heading" className="space-y-3">
      <h2 id="sources-heading" className="text-lg font-semibold text-stone-900">
        Sources <span className="text-sm font-normal text-stone-500">({sources.length})</span>
      </h2>

      <ol className="space-y-2">
        {sources.map((source, index) => (
          <li
            key={source.id}
            id={sourceAnchor(source.id)}
            className="scroll-mt-6 rounded-lg border border-stone-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-stone-500">
                  [{index + 1}] {source.domain}
                </p>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 block font-medium text-stone-900 underline decoration-stone-300 underline-offset-2 hover:decoration-stone-900"
                >
                  {source.title}
                </a>
              </div>

              <span className="flex shrink-0 flex-col items-end gap-1">
                <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-700">
                  {source.source_type}
                </span>
                {source.retrieval_method === "tavily_snippet" && (
                  <span
                    title="This page could not be scraped, so only the search snippet was available."
                    className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900"
                  >
                    Snippet only
                  </span>
                )}
              </span>
            </div>

            {source.snippet && (
              <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-stone-600">
                {source.snippet}
              </p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
