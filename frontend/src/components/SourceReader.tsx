"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { ApiError, getSource, getSources } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Source, SourceDetail } from "@/types/research";

export default function SourceReader({
  researchId,
  sourceId,
}: {
  researchId: string;
  sourceId: string;
}) {
  const [source, setSource] = useState<SourceDetail | null>(null);
  const [siblings, setSiblings] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The page keys this component by research+source id, so a new source gets a fresh
  // mount with loading=true. That is why the resets are not repeated here.
  useEffect(() => {
    let cancelled = false;

    Promise.all([getSource(researchId, sourceId), getSources(researchId)])
      .then(([detail, list]) => {
        if (cancelled) return;
        setSource(detail);
        setSiblings(list.sources ?? []);
        setLoading(false);
      })
      .catch((cause) => {
        if (cancelled) return;
        setLoading(false);
        if (cause instanceof ApiError && cause.status === 404) {
          setNotFound(true);
        } else {
          setError(
            cause instanceof ApiError ? cause.message : "Could not load this source.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [researchId, sourceId]);

  const position = siblings.findIndex((item) => item.id === sourceId);
  const previous = position > 0 ? siblings[position - 1] : null;
  const next =
    position >= 0 && position < siblings.length - 1 ? siblings[position + 1] : null;

  if (loading) {
    return (
      <div className="mx-auto w-full max-w-3xl space-y-4 px-4 py-10 sm:px-8">
        <div className="h-4 w-32 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-8 w-2/3 animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-4 w-1/3 animate-pulse rounded bg-zinc-100 dark:bg-zinc-900" />
        <div className="h-64 animate-pulse rounded-2xl bg-zinc-100 dark:bg-zinc-900" />
      </div>
    );
  }

  if (notFound || !source) {
    return (
      <div className="mx-auto w-full max-w-xl px-4 py-24 text-center">
        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          {notFound ? "Source not found" : "Could not load this source"}
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          {notFound
            ? "It may belong to a different research run."
            : error || "The server did not respond."}
        </p>
        <Link
          href={`/r/${researchId}`}
          className="mt-6 inline-flex rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Back to the research
        </Link>
      </div>
    );
  }

  const hasFullText = Boolean(source.content && source.content.trim());

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-16 pt-6 sm:px-8">
      <nav className="flex flex-wrap items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
        <Link
          href={`/r/${researchId}`}
          className="font-medium transition hover:text-zinc-800 dark:hover:text-zinc-200"
        >
          Research
        </Link>
        <span aria-hidden="true">/</span>
        <span>Source {source.index} of {source.total}</span>
      </nav>

      <header className="mt-4 space-y-3 border-b border-zinc-200/80 pb-5 dark:border-zinc-800">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700 ring-1 ring-inset ring-blue-600/20 dark:bg-blue-950/50 dark:text-blue-300 dark:ring-blue-500/30">
            [{source.index}]
          </span>
          <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
            {source.source_type}
          </span>
          <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
            {source.domain || "web"}
          </span>
          <span
            className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${
              hasFullText
                ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-500/30"
                : "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-500/30"
            }`}
          >
            {hasFullText ? "Full page text" : "Search snippet only"}
          </span>
          {source.retrieved_at && (
            <span className="text-[11px] text-zinc-400">
              Retrieved {formatDateTime(source.retrieved_at)}
            </span>
          )}
        </div>

        <h1 className="text-2xl font-bold leading-tight tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
          {source.title}
        </h1>

        <div className="flex flex-wrap items-center gap-2">
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Open original
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
          <span className="truncate text-[11px] text-zinc-400">{source.url}</span>
        </div>
      </header>

      {!hasFullText && (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-sm leading-relaxed text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
          This page could not be scraped, so the research used only the search
          snippet. The snippet below is the full evidence available for this source.
        </div>
      )}

      <div className="mt-6">
        {hasFullText ? (
          <div className="prose-paper">
            <ReactMarkdown
              components={{
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
              {source.content ?? ""}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="prose-paper whitespace-pre-wrap">{source.snippet}</p>
        )}
      </div>

      <nav className="mt-10 grid gap-3 border-t border-zinc-200/80 pt-5 sm:grid-cols-2 dark:border-zinc-800">
        {previous ? (
          <Link
            href={`/r/${researchId}/sources/${previous.id}`}
            className="group rounded-xl border border-zinc-200 bg-white p-3.5 transition hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-600"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
              Previous source
            </span>
            <span className="mt-1 block truncate text-sm font-medium text-zinc-800 group-hover:text-zinc-950 dark:text-zinc-200 dark:group-hover:text-white">
              {previous.title}
            </span>
          </Link>
        ) : (
          <span />
        )}
        {next && (
          <Link
            href={`/r/${researchId}/sources/${next.id}`}
            className="group rounded-xl border border-zinc-200 bg-white p-3.5 text-right transition hover:border-zinc-300 hover:shadow-sm sm:col-start-2 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-600"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
              Next source
            </span>
            <span className="mt-1 block truncate text-sm font-medium text-zinc-800 group-hover:text-zinc-950 dark:text-zinc-200 dark:group-hover:text-white">
              {next.title}
            </span>
          </Link>
        )}
      </nav>
    </div>
  );
}
