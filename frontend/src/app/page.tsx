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
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const closeStreamRef = useRef<(() => void) | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const stopStream = useCallback(() => {
    closeStreamRef.current?.();
    closeStreamRef.current = null;
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setReconnecting(false);
  }, []);

  useEffect(() => stopStream, [stopStream]);

  // Keyboard shortcut Ctrl+K for new research
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        handleNew();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

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
      setHistoryRefresh((n) => n + 1);
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

  /** Polling backstop to ensure UI never stalls. */
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
            // Keep polling; next tick may succeed
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
        setHistoryRefresh((n) => n + 1);
        setEvents([
          {
            stage: "queued",
            message: "Research queued",
            at: new Date().toISOString(),
          },
        ]);

        startPolling(research_id);

        closeStreamRef.current = streamResearch(research_id, {
          onStage: (event) => setEvents((prev) => appendEvent(prev, event)),
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
          setErrorMessage(status.error_message || "This research run failed.");
          setView("failed");
        } else {
          // Still running: attach stream & polling
          startPolling(id);
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
    <div className="flex h-screen w-full overflow-hidden bg-white text-zinc-900">
      {/* 1. Left Sidebar (ChatGPT / Claude styled) */}
      <aside
        className={`${
          sidebarOpen ? "w-72" : "w-0 -translate-x-full"
        } relative z-30 flex h-full shrink-0 flex-col border-r border-zinc-800 bg-[#18181b] p-3 text-zinc-100 transition-all duration-300 ease-in-out lg:static lg:translate-x-0`}
      >
        {/* App Logo & Title */}
        <div className="mb-4 flex items-center justify-between px-2 pt-1">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-md">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <span className="block text-sm font-semibold tracking-tight text-white">
                Research Agent
              </span>
              <span className="block text-[11px] text-zinc-400">
                Cited Fact-Checking
              </span>
            </div>
          </div>

          {/* Close sidebar on mobile / small screen */}
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white lg:hidden"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* History Component inside Sidebar */}
        <div className="flex-1 overflow-hidden">
          <History
            onSelect={handleSelect}
            activeId={researchId}
            refreshTrigger={historyRefresh}
            onNew={handleNew}
          />
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-20 bg-black/50 backdrop-blur-xs lg:hidden"
        />
      )}

      {/* 2. Main Canvas / Chat Area */}
      <div className="flex flex-1 flex-col h-full overflow-hidden bg-white">
        {/* Top Navbar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-zinc-200/80 px-4 sm:px-6 bg-white/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
              className="rounded-xl p-2 text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-900"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" />
              </svg>
            </button>

            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-zinc-900">
                AI Research Assistant
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-600">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Research Model
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {view !== "idle" && (
              <button
                type="button"
                onClick={handleNew}
                className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 shadow-xs transition hover:border-zinc-300 hover:bg-zinc-50"
              >
                <svg className="h-3.5 w-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                <span>New research</span>
              </button>
            )}
          </div>
        </header>

        {/* Scrollable Main Conversation / Report Stream */}
        <div ref={scrollAreaRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
          <div className="mx-auto max-w-3xl space-y-8 pb-32">
            {/* View: Idle (Claude / ChatGPT style welcome & input) */}
            {view === "idle" && (
              <ResearchForm onSubmit={handleSubmit} disabled={submitting} />
            )}

            {/* View: Running or Completed or Failed */}
            {view !== "idle" && (
              <>
                {/* User Prompt Message Bubble (ChatGPT / Claude style) */}
                <div className="flex items-start gap-3.5 rounded-2xl bg-zinc-50 p-4 border border-zinc-200/80 shadow-xs">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white shadow-xs">
                    You
                  </div>
                  <div className="flex-1 pt-0.5">
                    <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
                      Research Question
                    </p>
                    <p className="text-base font-medium text-zinc-900 leading-relaxed">
                      {query}
                    </p>
                  </div>
                </div>

                {/* Assistant Output Stream */}
                <div className="space-y-6">
                  {/* Research Activity Accordion / Timeline (Preserved exactly as user requested) */}
                  <ResearchProgress
                    events={events}
                    reconnecting={reconnecting}
                    failed={view === "failed"}
                  />

                  {/* Failed View Alert */}
                  {view === "failed" && (
                    <div className="rounded-2xl border border-red-200 bg-red-50/80 p-5 shadow-xs">
                      <div className="flex items-center gap-2 text-red-900 font-semibold text-sm">
                        <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Research could not be completed
                      </div>
                      <p className="mt-2 text-sm text-red-800 leading-relaxed">
                        {errorMessage || "An unexpected error occurred during research."}
                      </p>
                      <button
                        type="button"
                        onClick={handleNew}
                        className="mt-4 rounded-xl bg-zinc-900 px-4 py-2 text-xs font-medium text-white shadow transition hover:bg-zinc-700"
                      >
                        Try another question
                      </button>
                    </div>
                  )}

                  {/* Completed View: Full Markdown Report & Sources */}
                  {view === "completed" && result && (
                    <div className="space-y-8 pt-2">
                      <ResearchReport
                        title={result.title}
                        markdown={result.markdown}
                        sources={sources}
                      />
                      <SourceList sources={sources} />
                    </div>
                  )}

                  {view === "completed" && !result && (
                    <p className="text-sm text-zinc-500">
                      Research completed but produced no text output.
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* 3. Floating Bottom Prompt Bar (when in running or completed state) */}
        {view !== "idle" && (
          <div className="pointer-events-none sticky bottom-0 z-20 w-full bg-gradient-to-t from-white via-white/95 to-transparent pt-6 pb-4 px-4 sm:px-8">
            <div className="pointer-events-auto mx-auto max-w-3xl">
              <ResearchForm
                onSubmit={handleSubmit}
                disabled={submitting}
                compact={true}
              />
              <p className="mt-2 text-center text-[11px] text-zinc-400">
                Autonomous AI Research Agent · Verifies claims against live web sources
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function appendEvent(prev: ActivityEvent[], event: ActivityEvent): ActivityEvent[] {
  const last = prev[prev.length - 1];
  if (last && last.stage === event.stage && last.message === event.message) {
    return prev;
  }
  return [...prev, event];
}

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
