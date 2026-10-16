"use client";

import { useEffect, useState } from "react";

import { ApiError, getHistory } from "@/lib/api";
import type { HistoryItem } from "@/types/research";

export default function History({
  onSelect,
  activeId,
  refreshTrigger,
}: {
  onSelect: (researchId: string) => void;
  activeId: string | null;
  refreshTrigger?: number;
}) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <section aria-labelledby="history-heading" className="space-y-3">
      <h2 id="history-heading" className="text-sm font-semibold text-stone-900">
        Previous research
      </h2>

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
          {error}
        </p>
      ) : items === null ? (
        <p className="text-sm text-stone-500">Loading history…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-stone-500">
          Nothing here yet. Your research will appear in this list.
        </p>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item) => (
            <li key={item.research_id}>
              <button
                type="button"
                onClick={() => onSelect(item.research_id)}
                aria-current={item.research_id === activeId ? "true" : undefined}
                className={`w-full rounded-md border px-3 py-2 text-left transition ${
                  item.research_id === activeId
                    ? "border-stone-900 bg-stone-100"
                    : "border-stone-200 bg-white hover:border-stone-400 hover:bg-stone-50"
                }`}
              >
                <span className="line-clamp-2 block text-sm text-stone-800">
                  {item.query}
                </span>
                <span className="mt-1 flex items-center gap-2 text-xs text-stone-500">
                  <StatusDot status={item.status} />
                  {item.status}
                  {item.source_count > 0 && (
                    <span>· {item.source_count} sources</span>
                  )}
                  {item.created_at && (
                    <span>· {new Date(item.created_at).toLocaleDateString()}</span>
                  )}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "bg-emerald-600"
      : status === "failed"
        ? "bg-red-600"
        : status === "running"
          ? "bg-blue-600"
          : "bg-stone-400";
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-1.5 w-1.5 rounded-full ${color}`}
    />
  );
}
