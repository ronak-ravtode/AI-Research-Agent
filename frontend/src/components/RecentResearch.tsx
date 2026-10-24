"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { StatusDot } from "@/components/StatusBadge";
import { getHistory } from "@/lib/api";
import { formatRelativeDate } from "@/lib/format";
import type { HistoryItem } from "@/types/research";

export default function RecentResearch({
  activeId,
  refreshKey = 0,
  limit = 7,
  onNavigate,
}: {
  activeId: string | null;
  refreshKey?: string | number;
  limit?: number;
  onNavigate?: () => void;
}) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      getHistory({ limit })
        .then((body) => {
          if (cancelled) return;
          setItems(body.history ?? []);
          setError(false);
        })
        .catch(() => {
          if (!cancelled) setError(true);
        });
    };

    load();
    const interval = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [limit, refreshKey]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between px-2 pb-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
          Recent
        </h2>
        <Link
          href="/library"
          onClick={onNavigate}
          className="text-[11px] font-medium text-zinc-400 transition hover:text-white"
        >
          View all
        </Link>
      </div>

      <div className="no-scrollbar min-h-0 flex-1 space-y-0.5 overflow-y-auto px-1">
        {error ? (
          <p className="px-3 py-4 text-xs text-red-400">
            Could not load history.
          </p>
        ) : items === null ? (
          <div className="space-y-2 p-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-9 animate-pulse rounded-lg bg-zinc-800/50"
              />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs leading-relaxed text-zinc-500">
            No research yet.
            <br />
            Ask a question to get started.
          </p>
        ) : (
          <ul>
            {items.map((item) => {
              const isActive = item.research_id === activeId;
              return (
                <li key={item.research_id}>
                  <Link
                    href={`/r/${item.research_id}`}
                    onClick={onNavigate}
                    aria-current={isActive ? "page" : undefined}
                    className={`group flex flex-col rounded-lg px-2.5 py-2 text-left transition ${
                      isActive
                        ? "bg-zinc-800 text-white"
                        : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100"
                    }`}
                  >
                    <span className="flex items-start gap-1.5">
                      {item.parent_research_id && (
                        <svg
                          aria-label="Follow-up"
                          className="mt-0.5 h-3 w-3 shrink-0 text-blue-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a5 5 0 015 5v3m0 0l-3-3m3 3l3-3" />
                        </svg>
                      )}
                      <span className="line-clamp-2 flex-1 text-[12.5px] leading-snug">
                        {item.title || item.query}
                      </span>
                    </span>
                    <span className="mt-1 flex items-center gap-1.5 pl-0.5 text-[10.5px] text-zinc-500">
                      <StatusDot status={item.status} />
                      <span className="capitalize">{item.status}</span>
                      {item.source_count > 0 && (
                        <span>
                          · {item.source_count}{" "}
                          {item.source_count === 1 ? "source" : "sources"}
                        </span>
                      )}
                      <span className="ml-auto">
                        {formatRelativeDate(item.created_at)}
                      </span>
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
