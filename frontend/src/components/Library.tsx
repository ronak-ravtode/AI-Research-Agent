"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import StatusBadge from "@/components/StatusBadge";
import {
  ApiError,
  deleteResearch,
  getHistory,
  renameResearch,
} from "@/lib/api";
import {
  dateGroupLabel,
  formatDuration,
  formatRelativeDate,
} from "@/lib/format";
import type { HistoryItem, ResearchStatus } from "@/types/research";

const PAGE_SIZE = 20;

const FILTERS: { value: "all" | ResearchStatus; label: string }[] = [
  { value: "all", label: "All" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

export default function Library() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [filter, setFilter] = useState<"all" | ResearchStatus>("all");
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const requestRef = useRef(0);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(() => {
    const requestId = ++requestRef.current;
    setLoading(true);
    setError(null);
    getHistory({
      limit: PAGE_SIZE,
      offset: 0,
      status: filter === "all" ? undefined : filter,
      q: debounced || undefined,
    })
      .then((page) => {
        if (requestId !== requestRef.current) return;
        setItems(page.history ?? []);
        setTotal(page.total);
        setHasMore(page.has_more);
        setLoading(false);
      })
      .catch((cause) => {
        if (requestId !== requestRef.current) return;
        setError(
          cause instanceof ApiError ? cause.message : "Could not load the library.",
        );
        setLoading(false);
      });
  }, [debounced, filter]);

  useEffect(() => {
    // Deferred so `load`'s synchronous state writes do not cascade from the effect body.
    void Promise.resolve().then(load);
  }, [load]);

  function loadMore() {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    getHistory({
      limit: PAGE_SIZE,
      offset: items.length,
      status: filter === "all" ? undefined : filter,
      q: debounced || undefined,
    })
      .then((page) => {
        setItems((prev) => [...prev, ...(page.history ?? [])]);
        setTotal(page.total);
        setHasMore(page.has_more);
      })
      .catch(() => {
        // Keep the loaded page; the user can retry by clicking again.
      })
      .finally(() => setLoadingMore(false));
  }

  function startRename(item: HistoryItem) {
    setRenamingId(item.research_id);
    setRenameValue(item.title || item.query);
  }

  async function saveRename(item: HistoryItem) {
    const next = renameValue.trim();
    setRenamingId(null);
    if (next === (item.title || item.query)) return;

    setBusyId(item.research_id);
    try {
      const result = await renameResearch(item.research_id, next || null);
      setItems((prev) =>
        prev.map((entry) =>
          entry.research_id === item.research_id
            ? { ...entry, title: result.display_title || entry.query }
            : entry,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Could not rename this research.",
      );
    } finally {
      setBusyId(null);
    }
  }

  async function remove(item: HistoryItem) {
    const confirmed = window.confirm(
      `Delete “${item.title || item.query}”? Its report and sources are removed too. This cannot be undone.`,
    );
    if (!confirmed) return;

    setBusyId(item.research_id);
    try {
      await deleteResearch(item.research_id);
      setItems((prev) => prev.filter((entry) => entry.research_id !== item.research_id));
      setTotal((value) => Math.max(0, value - 1));
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Could not delete this research.",
      );
    } finally {
      setBusyId(null);
    }
  }

  // Precompute the date group and whether each row starts a new group, so rendering does
  // not have to mutate a variable mid-map.
  const rows = items.map((item, index) => {
    const group = dateGroupLabel(item.created_at);
    const previous = index > 0 ? dateGroupLabel(items[index - 1].created_at) : null;
    return { item, group, showGroup: group !== previous };
  });

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-950 dark:text-zinc-50">
            All research
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            {total} {total === 1 ? "run" : "runs"} saved
            {filter !== "all" || debounced ? " matching this view" : ""}.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-xl bg-zinc-900 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New research
        </Link>
      </div>

      {/* Controls */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="no-scrollbar -mx-1 flex gap-1 overflow-x-auto px-1">
          {FILTERS.map((option) => {
            const active = filter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                aria-pressed={active}
                onClick={() => setFilter(option.value)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  active
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>

        <div className="relative w-full sm:w-72">
          <svg className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search questions and titles…"
            aria-label="Search research"
            className="focus-ring w-full rounded-lg border border-zinc-200 bg-white py-2 pl-9 pr-8 text-sm text-zinc-800 placeholder-zinc-400 outline-none transition focus:border-zinc-400 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-zinc-600"
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              aria-label="Clear search"
              className="absolute right-2 top-2 rounded p-0.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mt-5 flex items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-xs font-medium underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* List */}
      <div className="mt-6">
        {loading ? (
          <ul className="space-y-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <li
                key={index}
                className="h-[74px] animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-900"
              />
            ))}
          </ul>
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-300 px-6 py-16 text-center dark:border-zinc-700">
            <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              {debounced || filter !== "all"
                ? "Nothing matches this view."
                : "No research yet."}
            </p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-zinc-500 dark:text-zinc-400">
              {debounced || filter !== "all"
                ? "Try a different search or status filter."
                : "Ask a question and it will appear here, shareable by URL."}
            </p>
            {!debounced && filter === "all" && (
              <Link
                href="/"
                className="mt-5 inline-flex rounded-xl bg-zinc-900 px-4 py-2 text-xs font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Start researching
              </Link>
            )}
          </div>
        ) : (
          <ul className="space-y-2">
            {rows.map(({ item, group, showGroup }) => {
              const busy = busyId === item.research_id;
              const renaming = renamingId === item.research_id;

              return (
                <li key={item.research_id}>
                  {showGroup && (
                    <p className="mb-2 mt-6 text-[11px] font-semibold uppercase tracking-wider text-zinc-400 first:mt-0">
                      {group}
                    </p>
                  )}

                  <div
                    className={`group rounded-xl border border-zinc-200 bg-white p-4 transition hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700 ${
                      busy ? "opacity-60" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        {renaming ? (
                          <form
                            onSubmit={(event) => {
                              event.preventDefault();
                              void saveRename(item);
                            }}
                            className="flex items-center gap-2"
                          >
                            <input
                              autoFocus
                              value={renameValue}
                              onChange={(event) => setRenameValue(event.target.value)}
                              onKeyDown={(event) => {
                                if (event.key === "Escape") setRenamingId(null);
                              }}
                              onBlur={() => void saveRename(item)}
                              aria-label="Research title"
                              className="w-full rounded-lg border border-zinc-300 bg-white px-2.5 py-1.5 text-sm text-zinc-900 outline-none focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
                            />
                            <button
                              type="submit"
                              className="shrink-0 rounded-lg bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
                            >
                              Save
                            </button>
                          </form>
                        ) : (
                          <Link
                            href={`/r/${item.research_id}`}
                            className="line-clamp-2 text-sm font-semibold leading-snug text-zinc-900 transition hover:text-blue-700 dark:text-zinc-100 dark:hover:text-blue-400"
                          >
                            {item.title || item.query}
                          </Link>
                        )}

                        {!renaming && item.title && item.title !== item.query && (
                          <p className="mt-1 line-clamp-1 text-xs text-zinc-500 dark:text-zinc-400">
                            {item.query}
                          </p>
                        )}

                        <div className="mt-2 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[11px] text-zinc-500 dark:text-zinc-400">
                          <StatusBadge status={item.status} />
                          {item.source_count > 0 && (
                            <span>
                              {item.source_count}{" "}
                              {item.source_count === 1 ? "source" : "sources"}
                            </span>
                          )}
                          {item.has_report && <span>report</span>}
                          {item.parent_research_id && <span>follow-up</span>}
                          <span>{formatRelativeDate(item.created_at)}</span>
                          {item.completed_at && (
                            <span>
                              took {formatDuration(item.created_at, item.completed_at)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-1">
                        <Link
                          href={`/r/${item.research_id}`}
                          className="rounded-lg px-2 py-1 text-[11px] font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                        >
                          Open
                        </Link>
                        <button
                          type="button"
                          onClick={() => startRename(item)}
                          aria-label="Rename"
                          title="Rename"
                          className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M11 4H4v16h16v-7M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4z" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          onClick={() => void remove(item)}
                          aria-label="Delete"
                          title="Delete"
                          className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 dark:hover:text-red-400"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.87 12.14A2 2 0 0116.14 21H7.86a2 2 0 01-1.99-1.86L5 7m5 4v6m4-6v6M9 7V4h6v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        {hasMore && !loading && (
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={loadMore}
              disabled={loadingMore}
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
            >
              {loadingMore && (
                <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              Load more ({total - items.length} remaining)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
