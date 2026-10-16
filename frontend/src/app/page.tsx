"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import History from "@/components/History";
import ResearchForm from "@/components/ResearchForm";
import ResearchProgress from "@/components/ResearchProgress";
import ResearchReport from "@/components/ResearchReport";
import SourceList from "@/components/SourceList";
import {
  ApiError,
  getActivity,
  getResearchStatus,
  getSources,
  startResearch,
  streamResearch,
} from "@/lib/api";
import type {
  ActivityEvent,
  ResearchStatus,
  ResearchStatusResponse,
  Source,
} from "@/types/research";

type View = "idle" | "running" | "completed" | "failed";

interface Result {
  title: string;
  markdown: string;
}

export default function Home() {
  const [view, setView] = useState<View>("idle");
  const [researchId, setResearchId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const closeStreamRef = useRef<(() => void) | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopStream = useCallback(() => {
    closeStreamRef.current?.();
    closeStreamRef.current = null;
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setReconnecting(false);
  }, []);

  // Never leave a stream running after the page unmounts.
  useEffect(() => stopStream, [stopStream]);

  /** Load everything a finished run needs. */
  const loadResult = useCallback(async (id: string) => {
    try {
      const [status, loadedSources] = await Promise.all([
        getResearchStatus(id),
        getSources(id),
      ]);
      setSources(loadedSources.sources ?? []);
      if (status.report_markdown) {
        setResult({
          title: status.report_title ?? status.query,
          markdown: status.report_markdown,
        });
      }
      if (status.error_message) setErrorMessage(status.error_message);
    } catch (cause) {
      setErrorMessage(
        cause instanceof ApiError ? cause.message : "Could not load the result.",
      );
    }
  }, []);

  /** Settle the UI once a run reaches a terminal state. */
  const finish = useCallback(
    async (id: string, status: ResearchStatus, error?: string | null) => {
      stopStream();
      if (status === "completed") {
        await loadResult(id);
        setView("completed");
      } else {
        setErrorMessage(
          error || "Research could not be completed. Please try again.",
        );
        setView("failed");
      }
    },
    [loadResult, stopStream],
  );

  /** Fallback used when the event stream cannot be relied on. */
  const startPolling = useCallback(
    (id: string) => {
      if (pollRef.current) return;
      pollRef.current = setInterval(() => {
        void (async () => {
          try {
            const status = await getResearchStatus(id);
            if (status.progress_message) {
              setEvents((prev) => appendStage(prev, status));
            }
            if (status.status === "completed" || status.status === "failed") {
              await finish(id, status.status, status.error_message);
            }
          } catch {
            // Keep polling; the next tick may succeed.
          }
        })();
      }, 2000);
    },
    [finish],
  );

  const handleSubmit = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (trimmed.length < 10 || submitting) return;

      stopStream();
      setSubmitting(true);
      setErrorMessage(null);
      setEvents([]);
      setSources([]);
      setResult(null);
      setQuery(trimmed);
      setView("running");

      try {
        const { research_id } = await startResearch(trimmed);
        setResearchId(research_id);
        setEvents([
          {
            stage: "queued",
            message: "Research queued",
            at: new Date().toISOString(),
          },
        ]);

        closeStreamRef.current = streamResearch(research_id, {
          onStage: (event) =>
            setEvents((prev) => appendEvent(prev, event)),
          onComplete: (event) => {
            void finish(research_id, event.status, event.message ?? null);
          },
          onError: (message) => {
            void finish(research_id, "failed", message);
          },
          onDisconnected: () => {
            setReconnecting(true);
            startPolling(research_id);
          },
        });
      } catch (cause) {
        setSubmitting(false);
        setView("failed");
        setErrorMessage(
          cause instanceof ApiError ? cause.message : "Could not start research.",
        );
        return;
      }

      setSubmitting(false);
    },
    [finish, startPolling, stopStream, submitting],
  );

  /** Reopen a saved run from history. */
  const handleSelect = useCallback(
    async (id: string) => {
      stopStream();
      setResearchId(id);
      setErrorMessage(null);
      setResult(null);
      setView("running");

      try {
        const [status, activity] = await Promise.all([
          getResearchStatus(id),
          getActivity(id),
        ]);
        setQuery(status.query);
        setEvents(
          activity.length
            ? activity
            : status.progress_message
              ? [
                  {
                    stage: status.current_stage ?? "queued",
                    message: status.progress_message,
                    at: status.updated_at,
                  },
                ]
              : [],
        );

        if (status.status === "completed") {
          await loadResult(id);
          setView("completed");
        } else if (status.status === "failed") {
          setErrorMessage(
            status.error_message || "This research run failed.",
          );
          setView("failed");
        } else {
          // Still running: attach to the live stream.
          closeStreamRef.current = streamResearch(id, {
            onStage: (event) => setEvents((prev) => appendEvent(prev, event)),
            onComplete: (event) => {
              void finish(id, event.status, event.message ?? null);
            },
            onError: (message) => void finish(id, "failed", message),
            onDisconnected: () => {
              setReconnecting(true);
              startPolling(id);
            },
          });
        }
      } catch (cause) {
        setView("failed");
        setErrorMessage(
          cause instanceof ApiError ? cause.message : "Could not open that research.",
        );
      }
    },
    [finish, loadResult, startPolling, stopStream],
  );

  const handleNew = useCallback(() => {
    stopStream();
    setView("idle");
    setResearchId(null);
    setQuery("");
    setEvents([]);
    setSources([]);
    setResult(null);
    setErrorMessage(null);
  }, [stopStream]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
      <header className="border-b border-stone-200 pb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">
          AI Research Assistant
        </h1>
        <p className="mt-1 text-sm text-stone-600">
          Web research with cited sources — every citation opens a real page.
        </p>
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <main className="min-w-0 space-y-8">
          {view === "idle" && (
            <ResearchForm onSubmit={handleSubmit} disabled={submitting} />
          )}

          {view === "running" && query && (
            <>
              <p className="text-sm leading-relaxed text-stone-600">
                <span className="font-medium text-stone-900">Researching:</span>{" "}
                {query}
              </p>
              <ResearchProgress
                events={events}
                reconnecting={reconnecting}
                failed={false}
              />
              {sources.length > 0 && <SourceList sources={sources} />}
            </>
          )}

          {view === "failed" && (
            <section className="rounded-lg border border-red-200 bg-red-50 p-6">
              <h2 className="text-lg font-semibold text-red-900">
                Research could not be completed
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-red-800">
                {errorMessage}
              </p>
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  onClick={handleNew}
                  className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-stone-700"
                >
                  Try again
                </button>
              </div>
            </section>
          )}

          {view === "completed" && result && (
            <>
              <ResearchProgress events={events} reconnecting={false} failed={false} />
              <ResearchReport
                title={result.title}
                markdown={result.markdown}
                sources={sources}
              />
              <SourceList sources={sources} />
            </>
          )}

          {view === "completed" && !result && (
            <p className="text-sm text-stone-600">
              This research finished but produced no report.
            </p>
          )}

          {view !== "idle" && (
            <button
              type="button"
              onClick={handleNew}
              className="text-sm font-medium text-stone-600 underline decoration-stone-300 underline-offset-4 hover:text-stone-900 hover:decoration-stone-900"
            >
              + New research
            </button>
          )}
        </main>

        <aside className="min-w-0">
          <History onSelect={handleSelect} activeId={researchId} />
        </aside>
      </div>
    </div>
  );
}

/** Append an SSE event, ignoring a repeat of the message already on screen. */
function appendEvent(prev: ActivityEvent[], event: ActivityEvent): ActivityEvent[] {
  const last = prev[prev.length - 1];
  if (last && last.stage === event.stage && last.message === event.message) {
    return prev;
  }
  return [...prev, event];
}

/** Append a stage derived from a polled status, same de-duplication rule. */
function appendStage(
  prev: ActivityEvent[],
  status: ResearchStatusResponse,
): ActivityEvent[] {
  if (!status.current_stage || !status.progress_message) return prev;
  return appendEvent(prev, {
    stage: status.current_stage,
    message: status.progress_message,
    at: new Date().toISOString(),
  });
}
