"use client";

import { useState } from "react";

interface Props {
  onSubmit: (query: string, depth: string) => void;
  loading: boolean;
}

const DEPTH_OPTIONS = [
  { value: "quick", label: "Quick", desc: "~1 iteration, 3-5 sources" },
  { value: "standard", label: "Standard", desc: "~2 iterations, 8-15 sources" },
  { value: "deep", label: "Deep", desc: "~4 iterations, 15-25 sources" },
];

export default function ResearchForm({ onSubmit, loading }: Props) {
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState("standard");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 10 && !loading) {
      onSubmit(query.trim(), depth);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Research Question
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What is the impact of generative AI on software development?"
          rows={3}
          className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-[#ededed] placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
          disabled={loading}
        />
        <p className="text-xs text-gray-500 mt-1">{query.length}/2000 (min 10)</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Research Depth
        </label>
        <div className="flex gap-2">
          {DEPTH_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setDepth(opt.value)}
              disabled={loading}
              className={`flex-1 px-3 py-2 rounded-lg text-sm border transition-colors ${
                depth === opt.value
                  ? "bg-blue-600 border-blue-500 text-white"
                  : "bg-[#1a1a1a] border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >
              <div className="font-medium">{opt.label}</div>
              <div className="text-xs opacity-70">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || query.trim().length < 10}
        className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
      >
        {loading ? "Researching..." : "Start Research"}
      </button>
    </form>
  );
}
