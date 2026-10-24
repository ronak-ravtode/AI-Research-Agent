"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ApiError,
  cancelResearch,
  getActivity,
  getResearchStatus,
  getSources,
  streamResearch,
} from "@/lib/api";
import type {
  ActivityEvent,
  ResearchStatus,
  ResearchStatusResponse,
  Source,
} from "@/types/research";

const TERMINAL: ResearchStatus[] = ["completed", "failed", "cancelled"];
const POLL_MS = 2500;

export interface ResearchState {
  status: ResearchStatusResponse | null;
  events: ActivityEvent[];
  sources: Source[];
  loading: boolean;
  notFound: boolean;
  error: string | null;
  reconnecting: boolean;
  stopping: boolean;
}

/**
 * Owns one run's live state: initial load, SSE, a polling backstop, cancellation, and
 * reloading the final payload. Shared by the run page and anything that embeds a run.
 */
export function useResearch(id: string | null) {
  const [status, setStatus] = useState<ResearchStatusResponse | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(Boolean(id));
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [stopping, setStopping] = useState(false);

  const closeRef = useRef<(() => void) | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const aliveRef = useRef(true);
  const idRef = useRef<string | null>(id);

  const stopTransports = useCallback(() => {
    closeRef.current?.();
    closeRef.current = null;
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  /**
   * Adopt the server's timeline, but never let it shrink: the backend commits each stage
   * row as it happens, so its copy is authoritative, while a stale in-flight fetch must
   * not drop events SSE already delivered.
   */
  const syncActivity = useCallback((activity: ActivityEvent[]) => {
    setEvents((prev) => (activity.length >= prev.length ? activity : prev));
  }, []);

  const reload = useCallback(
    async (researchId: string) => {
      const [fresh, loadedSources, activity] = await Promise.all([
        getResearchStatus(researchId),
        getSources(researchId),
        getActivity(researchId),
      ]);
      if (!aliveRef.current || idRef.current !== researchId) return null;
      setStatus(fresh);
      setSources(loadedSources.sources ?? []);
      syncActivity(activity);
      if (fresh.error_message) setError(fresh.error_message);
      return fresh;
    },
    [syncActivity],
  );

  /** Settle the UI once a run reaches a terminal state. */
  const finish = useCallback(
    async (researchId: string) => {
      stopTransports();
      setReconnecting(false);
      setStopping(false);
      try {
        await reload(researchId);
      } catch (cause) {
        if (!aliveRef.current) return;
        setError(
          cause instanceof ApiError
            ? cause.message
            : "Could not load the final result.",
        );
      }
    },
    [reload, stopTransports],
  );

  /**
   * Polling backstop. The Next.js rewrite that fronts `/api/*` buffers SSE responses in
   * development, so the stream cannot be the only source of live updates: like the status
   * row, the timeline is refreshed on this tick, which is what keeps the activity feed
   * moving while a run is in flight.
   */
  const startPolling = useCallback(
    (researchId: string) => {
      if (pollRef.current) return;
      pollRef.current = setInterval(() => {
        void (async () => {
          try {
            const [next, activity] = await Promise.all([
              getResearchStatus(researchId),
              getActivity(researchId),
            ]);
            if (!aliveRef.current || idRef.current !== researchId) return;
            setStatus(next);
            syncActivity(activity);
            if (next.status === "running" || next.status === "queued") {
              setStopping(Boolean(next.progress_message?.includes("cancel")));
            }
            if (TERMINAL.includes(next.status)) {
              await finish(researchId);
            }
          } catch {
            // Keep polling; the next tick may succeed.
          }
        })();
      }, POLL_MS);
    },
    [finish, syncActivity],
  );

  const connect = useCallback(
    (researchId: string) => {
      closeRef.current?.();
      closeRef.current = streamResearch(researchId, {
        onStage: (event) => setEvents((prev) => appendEvent(prev, event)),
        onComplete: () => {
          void finish(researchId);
        },
        onError: (message) => {
          setError(message);
          void finish(researchId);
        },
        onDisconnected: () => {
          setReconnecting(true);
          startPolling(researchId);
        },
      });
    },
    [finish, startPolling],
  );

  useEffect(() => {
    aliveRef.current = true;
    idRef.current = id;

    if (!id) return;

    let cancelled = false;
    stopTransports();

    void (async () => {
      // The page keys this hook by id, so a new run mounts fresh. These resets are kept
      // for safety when the hook is reused without remounting.
      setLoading(true);
      setNotFound(false);
      setError(null);
      setStatus(null);
      setSources([]);
      setEvents([]);

      try {
        const [initial, loadedSources, activity] = await Promise.all([
          getResearchStatus(id),
          getSources(id),
          getActivity(id),
        ]);
        if (cancelled) return;

        setStatus(initial);
        setSources(loadedSources.sources ?? []);
        setEvents(activity);
        if (initial.error_message) setError(initial.error_message);
        setLoading(false);

        if (!TERMINAL.includes(initial.status)) {
          startPolling(id);
          connect(id);
        }
      } catch (cause) {
        if (cancelled) return;
        setLoading(false);
        if (cause instanceof ApiError && cause.status === 404) {
          setNotFound(true);
        } else {
          setError(
            cause instanceof ApiError ? cause.message : "Could not load this research.",
          );
        }
      }
    })();

    return () => {
      cancelled = true;
      aliveRef.current = false;
      stopTransports();
    };
  }, [id, connect, startPolling, stopTransports]);

  const stop = useCallback(async () => {
    if (!id) return;
    setStopping(true);
    try {
      const result = await cancelResearch(id);
      if (TERMINAL.includes(result.status as ResearchStatus)) {
        await finish(id);
      }
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Could not cancel this research.",
      );
      setStopping(false);
    }
  }, [finish, id]);

  return {
    status,
    events,
    sources,
    loading,
    notFound,
    error,
    reconnecting,
    stopping,
    stop,
    reload: () => (id ? finish(id) : Promise.resolve()),
  };
}

function appendEvent(
  prev: ActivityEvent[],
  event: ActivityEvent,
): ActivityEvent[] {
  const last = prev[prev.length - 1];
  if (last && last.stage === event.stage && last.message === event.message) {
    return prev;
  }
  return [...prev, event];
}
