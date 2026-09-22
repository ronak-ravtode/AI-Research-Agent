"use client";

import { useState, useCallback } from "react";
import ResearchForm from "@/components/ResearchForm";
import ProgressStream from "@/components/ProgressStream";
import Results from "@/components/Results";
import History from "@/components/History";
import { startResearch } from "@/lib/api";

type ViewState = "form" | "running" | "done";

export default function Home() {
  const [view, setView] = useState<ViewState>("form");
  const [researchId, setResearchId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (query: string, depth: string) => {
    setError(null);
    try {
      const result = await startResearch(query, depth);
      setResearchId(result.research_id);
      setView("running");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start research");
    }
  };

  const handleStatusChange = useCallback((status: string) => {
    if (status === "completed" || status === "failed") {
      setView("done");
    }
  }, []);

  const handleHistorySelect = (id: string) => {
    setResearchId(id);
    setView("done");
  };

  const handleNew = () => {
    setView("form");
    setResearchId(null);
    setError(null);
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Research</h2>
        {view !== "form" && (
          <button
            onClick={handleNew}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            + New Research
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {view === "form" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-[#111] border border-gray-800 rounded-lg p-4">
              <ResearchForm onSubmit={handleSubmit} loading={false} />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">Recent History</h3>
            <History onSelect={handleHistorySelect} />
          </div>
        </div>
      )}

      {view === "running" && researchId && (
        <div className="space-y-6">
          <div className="bg-[#111] border border-gray-800 rounded-lg p-4">
            <ProgressStream researchId={researchId} onStatusChange={handleStatusChange} />
          </div>
        </div>
      )}

      {view === "done" && researchId && (
        <div className="space-y-6">
          <div className="bg-[#111] border border-gray-800 rounded-lg p-4">
            <Results researchId={researchId} />
          </div>
        </div>
      )}
    </div>
  );
}
