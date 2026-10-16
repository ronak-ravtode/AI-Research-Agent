"use client";

import { useEffect, useRef } from "react";

import type { ActivityEvent, Stage } from "@/types/research";

const STAGE_LABEL: Record<Stage, string> = {
  queued: "Queued",
  planning: "Planning the search",
  searching: "Searching the web",
  reading: "Reading sources",
  writing: "Writing the answer",
  complete: "Finished",
};

const SPINNER_STAGES: Stage[] = ["queued", "planning", "searching", "reading", "writing"];

export default function ResearchProgress({
  events,
  reconnecting,
  failed,
}: {
  events: ActivityEvent[];
  reconnecting: boolean;
  failed: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length]);

  const current = events.length ? events[events.length - 1].stage : "queued";
  const busy = !failed && SPINNER_STAGES.includes(current);

  return (
    <section aria-labelledby="progress-heading" className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2
          id="progress-heading"
          className="text-lg font-semibold text-stone-900"
        >
          Research activity
        </h2>
        {reconnecting && (
          <span
            role="status"
            className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-900"
          >
            Reconnecting to research updates…
          </span>
        )}
      </div>

      {events.length === 0 ? (
        <p className="text-sm text-stone-500">Waiting for the first update…</p>
      ) : (
        <ol className="space-y-0" aria-live="polite" aria-busy={busy}>
          {events.map((event, index) => {
            const isLast = index === events.length - 1;
            const time = event.at ? formatTime(event.at) : "";
            return (
              <li key={`${index}-${event.stage}`} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <span
                    aria-hidden="true"
                    className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${
                      isLast && busy
                        ? "animate-pulse bg-stone-900"
                        : failed && isLast
                          ? "bg-red-600"
                          : "bg-stone-400"
                    }`}
                  />
                  {!isLast && (
                    <span aria-hidden="true" className="w-px flex-1 bg-stone-200" />
                  )}
                </div>
                <div className="pb-5">
                  <p className="text-sm font-medium text-stone-900">
                    {event.message}
                  </p>
                  <p className="mt-0.5 text-xs text-stone-500">
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
    </section>
  );
}

function formatTime(iso: string): string {
  const date = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
