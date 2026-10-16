"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError, getHistory } from "@/lib/api";
import type { HistoryItem } from "@/types/research";

export default function History({
  onSelect,
  activeId,
  refreshTrigger,
  onNew,
}: {
  onSelect: (researchId: string) => void;
  activeId: string | null;
  refreshTrigger?: number;
  onNew?: () => void;
}) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;

    const fetchHistory = () => {
      getHistory()
        .then((body) => {
          if (!cancelled) {
            setItems(body.history ?? []);
            setError(null);
          }
        })
        .catch((cause: unknown) => {
          if (cancelled) return;
          setError(
            cause instanceof ApiError
              ? cause.message
              : "Could not load history.",
          );
        });
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [refreshTrigger]);

  const filteredItems = useMemo(() => {
    if (!items) return [];
    if (!search.trim()) return items;
    const query = search.toLowerCase();
    return items.filter((item) => item.query.toLowerCase().includes(query));
  }, [items, search]);

  return (
    <div className="flex h-full flex-col">
      {/* Top action: + New Research */}
      {onNew && (
        <div className="mb-3 px-1">
          <button
            type="button"
            onClick={onNew}
            className="flex w-full items-center justify-between rounded-xl border border-zinc-700/60 bg-zinc-800/80 px-3.5 py-2.5 text-sm font-medium text-zinc-100 shadow-sm transition hover:border-zinc-500 hover:bg-zinc-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4 text-zinc-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              New research
            </span>
            <span className="text-[11px] font-normal text-zinc-400">Ctrl+K</span>
          </button>
        </div>
      )}

      {/* Search filter for history */}
      <div className="mb-3 px-1">
        <div className="relative">
          <svg
            className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search past research…"
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/90 py-1.5 pl-8 pr-3 text-xs text-zinc-200 placeholder-zinc-500 outline-none transition focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600"
          />
        </div>
      </div>

      {/* History section heading */}
      <div className="flex items-center justify-between px-2 pb-2">
        <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Previous research
        </h2>
        {items && (
          <span className="text-[11px] text-zinc-400">{filteredItems.length}</span>
        )}
      </div>

      {/* Scrollable List */}
      <div className="flex-1 overflow-y-auto px-1 space-y-1">
        {error ? (
          <div className="rounded-lg border border-red-900/50 bg-red-950/40 p-3 text-xs text-red-300">
            {error}
          </div>
        ) : items === null ? (
          <div className="space-y-2 p-2">
            <div className="h-10 animate-pulse rounded-lg bg-zinc-800/50" />
            <div className="h-10 animate-pulse rounded-lg bg-zinc-800/50" />
            <div className="h-10 animate-pulse rounded-lg bg-zinc-800/50" />
          </div>
        ) : filteredItems.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-zinc-400">
            {search ? "No matching research found." : "No previous research yet."}
          </p>
        ) : (
          <ul className="space-y-1">
            {filteredItems.map((item) => {
              const isActive = item.research_id === activeId;
              return (
                <li key={item.research_id}>
                  <button
                    type="button"
                    onClick={() => onSelect(item.research_id)}
                    aria-current={isActive ? "true" : undefined}
                    className={`group relative flex w-full flex-col items-start rounded-xl px-3 py-2.5 text-left text-xs transition ${
                      isActive
                        ? "bg-zinc-800 text-white font-medium shadow-sm ring-1 ring-zinc-700"
                        : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200"
                    }`}
                  >
                    <span className="line-clamp-2 w-full text-[13px] leading-snug">
                      {item.query}
                    </span>
                    <span className="mt-1.5 flex w-full items-center gap-2 text-[11px] text-zinc-400">
                      <span className="flex items-center gap-1.5">
                        <StatusDot status={item.status} />
                        <span className="capitalize">{item.status}</span>
                      </span>
                      {item.source_count > 0 && (
                        <span>· {item.source_count} sources</span>
                      )}
                      {item.created_at && (
                        <span className="ml-auto text-zinc-400">
                          {formatRelativeDate(item.created_at)}
                        </span>
                      )}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Bottom system footer in sidebar */}
      <div className="mt-auto border-t border-zinc-800/80 pt-3 px-2">
        <div className="flex items-center justify-between text-[11px] text-zinc-400">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Supabase + Groq
          </span>
          <span>v1.0.0</span>
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  let color = "bg-zinc-500";
  if (status === "completed") color = "bg-emerald-500";
  else if (status === "failed") color = "bg-red-500";
  else if (status === "running" || status === "planning" || status === "searching" || status === "reading") {
    color = "bg-blue-500 animate-pulse";
  } else if (status === "queued") {
    color = "bg-amber-400";
  }

  return (
    <span
      aria-hidden="true"
      className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${color}`}
    />
  );
}

function formatRelativeDate(iso: string): string {
  try {
    const date = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 24 && now.getDate() === date.getDate()) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}
