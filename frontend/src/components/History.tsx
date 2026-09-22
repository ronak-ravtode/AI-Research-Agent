"use client";

import { useEffect, useState } from "react";
import { getHistory, type HistoryItem } from "@/lib/api";

interface Props {
  onSelect: (researchId: string) => void;
}

const STATUS_COLORS: Record<string, string> = {
  completed: "text-green-400",
  failed: "text-red-400",
  planning: "text-yellow-400",
  researching: "text-blue-400",
};

export default function History({ onSelect }: Props) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then((data) => setHistory(data.history))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-500 text-sm py-4">Loading history...</div>;
  }

  if (history.length === 0) {
    return <div className="text-gray-500 text-sm py-4">No research history yet</div>;
  }

  return (
    <div className="space-y-2">
      {history.map((item) => (
        <button
          key={item.research_id}
          onClick={() => onSelect(item.research_id)}
          className="w-full text-left bg-[#111] border border-gray-800 rounded-lg p-3 hover:border-gray-600 transition-colors"
        >
          <div className="text-sm font-medium truncate">{item.query}</div>
          <div className="flex gap-3 mt-1 text-xs text-gray-500">
            <span className={STATUS_COLORS[item.status] || "text-gray-400"}>
              {item.status}
            </span>
            <span>{item.research_depth}</span>
            <span>{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
