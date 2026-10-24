"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import ResearchForm from "@/components/ResearchForm";
import ResearchProgress from "@/components/ResearchProgress";
import ResearchReport from "@/components/ResearchReport";
import SourceList from "@/components/SourceList";
import StatusBadge from "@/components/StatusBadge";
import VerificationPanel from "@/components/VerificationPanel";
import { startResearch } from "@/lib/api";
import {
  downloadMarkdown,
  formatDateTime,
  formatDuration,
} from "@/lib/format";
import { DEPTH_OPTIONS, depthFromIterations, usePreferences } from "@/lib/preferences";
import { useResearch } from "@/lib/useResearch";

export default function ResearchRun({ id }: { id: string }) {
  const router = useRouter();
  const { preferences } = usePreferences();
  const {
    status,
    events,
    sources,
    loading,
    notFound,
    error,
    reconnecting,
    stopping,
    stop,
  } = useResearch(id);

  const [copied, setCopied] = useState(false);
  const [startingFollowUp, setStartingFollowUp] = useState(false);
  const topRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    topRef.current?.scrollIntoView({ block: "start" });
  }, [id]);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard permission is optional.
    }
  }

  async function handleFollowUp(question: string) {
    if (!status || startingFollowUp) return;
    setStartingFollowUp(true);
    try {
      const { research_id } = await startResearch(question, {
        parentResearchId: id,
        maxIterations: DEPTH_OPTIONS[preferences.depth].iterations,
      });
      router.push(`/r/${research_id}`);
    } catch {
      setStartingFollowUp(false);
    }
  }

  async function handleRetry() {
    if (!status || startingFollowUp) return;
    setStartingFollowUp(true);
    try {
      const { research_id } = await startResearch(status.query, {
        maxIterations: DEPTH_OPTIONS[preferences.depth].iterations,
      });
      router.push(`/r/${research_id}`);
    } catch {
      setStartingFollowUp(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto w-full max-w-3xl space-y-5 px-4 py-10 sm:px-8">
        <div className="h-4 w-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-9 w-3/4 animate-pulse rounded-lg bg-zinc-200 dark:bg-zinc-800" />
        <div className="h-4 w-1/2 animate-pulse rounded bg-zinc-100 dark:bg-zinc-900" />
        <div className="h-40 animate-pulse rounded-2xl bg-zinc-100 dark:bg-zinc-900" />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="mx-auto w-full max-w-xl px-4 py-24 text-center">
        <p className="text-sm font-medium text-zinc-500">404</p>
        <h1 className="mt-2 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          That research does not exist
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          It may have been deleted, or the link may be wrong.
        </p>
        <Link
          href="/library"
          className="mt-6 inline-flex rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Go to library
        </Link>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="mx-auto w-full max-w-xl px-4 py-24 text-center">
        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
          Could not load this research
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          {error || "The server did not respond."}
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-6 rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Try again
        </button>
      </div>
    );
  }

  const isRunning = status.status === "running" || status.status === "queued";
  const isCompleted = status.status === "completed";
  const isFailed = status.status === "failed";
  const isCancelled = status.status === "cancelled";
  const title = status.display_title || status.report_title || status.query;
  const depth = depthFromIterations(status.max_iterations);
  const duration = formatDuration(status.created_at, status.completed_at);

  return (
    <div ref={topRef} className="mx-auto w-full max-w-3xl px-4 pb-40 pt-6 sm:px-8">
      <Link
        href="/library"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500 transition hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        All research
      </Link>

      {/* Run header */}
      <header className="mt-4 space-y-3 border-b border-zinc-200/80 pb-5 dark:border-zinc-800">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={status.status} />
          {status.parent_research_id && (
            <Link
              href={`/r/${status.parent_research_id}`}
              className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-[11px] font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20 transition hover:bg-blue-100 dark:bg-blue-950/40 dark:text-blue-300 dark:ring-blue-500/30"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a5 5 0 015 5v3m0 0l-3-3m3 3l3-3" />
              </svg>
              Follow-up
            </Link>
          )}
          {depth && (
            <span
              title={DEPTH_OPTIONS[depth].description}
              className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {DEPTH_OPTIONS[depth].label} depth
            </span>
          )}
          {sources.length > 0 && (
            <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
              {sources.length} {sources.length === 1 ? "source" : "sources"}
            </span>
          )}
          {duration && (
            <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
              · {isRunning ? "running " : ""}
              {duration}
            </span>
          )}
          <span className="ml-auto text-[11px] text-zinc-400">
            {formatDateTime(status.created_at)}
          </span>
        </div>

        <h1 className="text-2xl font-bold leading-tight tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
          {title}
        </h1>

        {status.display_title && (
          <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
            {status.query}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={copyLink}
            className="focus-ring inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-600 transition hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 13a5 5 0 007.07 0l1.41-1.41a5 5 0 00-7.07-7.07L10 5.93M14 11a5 5 0 00-7.07 0L5.5 12.41a5 5 0 007.07 7.07L14 18.07" />
            </svg>
            {copied ? "Link copied" : "Copy link"}
          </button>

          {isCompleted && status.report_markdown && (
            <button
              type="button"
              onClick={() =>
                downloadMarkdown(title, status.report_markdown ?? "")
              }
              className="focus-ring inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-600 transition hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3M4 19h16" />
              </svg>
              Export .md
            </button>
          )}

          {isRunning && (
            <button
              type="button"
              onClick={() => void stop()}
              disabled={stopping}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-medium text-red-700 transition hover:border-red-300 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300 dark:hover:bg-red-950"
            >
              {stopping ? (
                <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              ) : (
                <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="7" y="7" width="10" height="10" rx="1.5" />
                </svg>
              )}
              {stopping ? "Stopping…" : "Stop"}
            </button>
          )}

          {(isFailed || isCancelled) && (
            <button
              type="button"
              onClick={() => void handleRetry()}
              disabled={startingFollowUp}
              className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5M20 20v-5h-5M4 9a8 8 0 0114-3l2 2M20 15a8 8 0 01-14 3l-2-2" />
              </svg>
              Retry
            </button>
          )}
        </div>

        {status.planned_queries && status.planned_queries.length > 0 && (
          <div className="pt-1">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
              Planned queries
            </p>
            <ul className="flex flex-wrap gap-1.5">
              {status.planned_queries.map((planned) => (
                <li
                  key={planned}
                  className="rounded-full bg-zinc-100 px-2.5 py-1 text-[11px] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                >
                  {planned}
                </li>
              ))}
            </ul>
          </div>
        )}
      </header>

      <div className="space-y-6 pt-5">
        <ResearchProgress
          events={events}
          reconnecting={reconnecting}
          failed={isFailed}
          cancelled={isCancelled}
          initiallyCollapsed={isCompleted && !reconnecting}
        />

        {isCancelled && (
          <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
            <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Research stopped
            </p>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              No further work was performed. The activity above is everything that ran.
            </p>
          </div>
        )}

        {isFailed && (
          <div className="rounded-2xl border border-red-200 bg-red-50/80 p-5 dark:border-red-900/60 dark:bg-red-950/30">
            <p className="text-sm font-semibold text-red-900 dark:text-red-200">
              Research could not be completed
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-red-800 dark:text-red-300">
              {error || status.error_message || "An unexpected error occurred."}
            </p>
          </div>
        )}

        {isCompleted && status.report_markdown && (
          <VerificationPanel
            note={status.verification_note}
            revised={status.verification_revised}
            available={status.verification_available}
            removedClaims={status.removed_claims}
          />
        )}

        {isCompleted && status.report_markdown && (
          <ResearchReport
            researchId={id}
            title={status.report_title || status.query}
            markdown={status.report_markdown}
            sources={sources}
            citationPreview={preferences.citationPreview}
          />
        )}

        {isCompleted && !status.report_markdown && (
          <p className="text-sm text-zinc-500">
            Research completed but produced no text output.
          </p>
        )}

        {isCompleted && <SourceList researchId={id} sources={sources} />}
      </div>

      {isCompleted && (
        <div className="pointer-events-none sticky bottom-0 z-20 mt-8 bg-gradient-to-t from-white via-white/95 to-transparent pb-4 pt-6 dark:from-zinc-950 dark:via-zinc-950/95">
          <div className="pointer-events-auto">
            <ResearchForm
              onSubmit={handleFollowUp}
              disabled={startingFollowUp}
              compact
            />
            <p className="mt-2 text-center text-[11px] text-zinc-400">
              Follow-ups reuse this run&apos;s question, answer, and best sources.
              {" · "}
              <span className="capitalize">{preferences.depth}</span> depth
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
