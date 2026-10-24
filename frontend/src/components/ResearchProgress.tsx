"use client";

import { useEffect, useRef, useState } from "react";

import { formatClock } from "@/lib/format";
import type { ActivityEvent, Stage } from "@/types/research";

const STAGE_LABEL: Record<Stage, string> = {
  queued: "Queued",
  planning: "Planning the search",
  searching: "Searching the web",
  reading: "Reading sources",
  deciding: "Judging the evidence",
  writing: "Writing the answer",
  verifying: "Verifying claims",
  complete: "Finished",
};

const SPINNER_STAGES: Stage[] = [
  "queued",
  "planning",
  "searching",
  "reading",
  "deciding",
  "writing",
  "verifying",
];

export default function ResearchProgress({
  events,
  reconnecting,
  failed,
  cancelled = false,
  initiallyCollapsed = false,
}: {
  events: ActivityEvent[];
  reconnecting: boolean;
  failed: boolean;
  cancelled?: boolean;
  initiallyCollapsed?: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const [collapsed, setCollapsed] = useState(initiallyCollapsed);

  useEffect(() => {
    if (collapsed) return;
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length, collapsed]);

  const current = events.length ? events[events.length - 1].stage : "queued";
  const busy =
    !failed && !cancelled && SPINNER_STAGES.includes(current) && current !== "complete";
  const isFinished = !failed && !cancelled && current === "complete";

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-50/70 shadow-sm transition-all dark:border-zinc-800 dark:bg-zinc-900/40">
      <div
        className="flex cursor-pointer items-center justify-between gap-3 border-b border-zinc-200/80 bg-white/70 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900/60"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex min-w-0 items-center gap-2.5">
          {busy ? (
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            </span>
          ) : failed ? (
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </span>
          ) : cancelled ? (
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                <rect x="7" y="7" width="10" height="10" rx="1.5" />
              </svg>
            </span>
          ) : (
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          )}

          <h2 className="shrink-0 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Research activity
          </h2>

          <span className="shrink-0 rounded-full bg-zinc-200/70 px-2 py-0.5 text-[11px] font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            {events.length} {events.length === 1 ? "step" : "steps"}
          </span>
        </div>

        <div className="flex min-w-0 items-center gap-3">
          {reconnecting && (
            <span
              role="status"
              className="shrink-0 animate-pulse rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-medium text-amber-900 dark:bg-amber-950/60 dark:text-amber-300"
            >
              Reconnecting…
            </span>
          )}

          {busy && (
            <span className="hidden truncate text-xs font-medium text-blue-700 sm:block dark:text-blue-300">
              {events[events.length - 1]?.message}…
            </span>
          )}

          <button
            type="button"
            aria-label={collapsed ? "Expand activity" : "Collapse activity"}
            aria-expanded={!collapsed}
            className="shrink-0 rounded-lg p-1 text-zinc-400 hover:bg-zinc-200/60 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
          >
            <svg
              className={`h-4 w-4 transition-transform ${collapsed ? "-rotate-90" : "rotate-0"}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4 sm:p-5">
          {events.length === 0 ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Waiting for the first update…
            </p>
          ) : (
            <ol className="space-y-0" aria-live="polite" aria-busy={busy}>
              {events.map((event, index) => {
                const isLast = index === events.length - 1;
                const time = formatClock(event.at);
                return (
                  <li key={`${index}-${event.stage}`} className="flex gap-3.5">
                    <div className="flex flex-col items-center">
                      <span
                        aria-hidden="true"
                        className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full transition-all ${
                          isLast && busy
                            ? "bg-blue-600 ring-4 ring-blue-100 dark:ring-blue-950"
                            : failed && isLast
                              ? "bg-red-600"
                              : cancelled && isLast
                                ? "bg-zinc-500"
                                : isFinished && isLast
                                  ? "bg-emerald-600 ring-4 ring-emerald-100 dark:ring-emerald-950"
                                  : "bg-zinc-400 dark:bg-zinc-600"
                        }`}
                      />
                      {!isLast && (
                        <span aria-hidden="true" className="my-0.5 w-px flex-1 bg-zinc-200 dark:bg-zinc-700" />
                      )}
                    </div>
                    <div className="pb-4">
                      <p className="text-sm font-medium leading-snug text-zinc-900 dark:text-zinc-100">
                        {event.message}
                      </p>
                      <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
                        {STAGE_LABEL[event.stage] ?? event.stage}
                        {time ? ` · ${time}` : ""}
                      </p>
                    </div>
                  </li>
                );
              })}
              <div ref={endRef} />
            </ol>
          )}
        </div>
      )}
    </div>
  );
}
