"use client";

import { useEffect, useState } from "react";
import { getReport, getSources, type Report, type Source } from "@/lib/api";

interface Props {
  researchId: string;
}

export default function Results({ researchId }: Props) {
  const [report, setReport] = useState<Report | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"report" | "sources">("report");

  useEffect(() => {
    async function load() {
      try {
        const [reportData, sourcesData] = await Promise.all([
          getReport(researchId),
          getSources(researchId),
        ]);
        setReport(reportData);
        setSources(sourcesData.sources);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load results");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [researchId]);

  if (loading) {
    return (
      <div className="text-center py-8 text-gray-400">Loading results...</div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-300">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setTab("report")}
          className={`px-3 py-1 text-sm rounded ${tab === "report" ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"}`}
        >
          Report ({report?.title ? "1" : "0"})
        </button>
        <button
          onClick={() => setTab("sources")}
          className={`px-3 py-1 text-sm rounded ${tab === "sources" ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"}`}
        >
          Sources ({sources.length})
        </button>
      </div>

      {tab === "report" && report && (
        <div className="bg-[#111] border border-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">{report.title}</h3>
          <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap text-gray-300 leading-relaxed">
            {report.content}
          </div>
        </div>
      )}

      {tab === "report" && !report && (
        <div className="text-gray-500 text-center py-8">No report generated</div>
      )}

      {tab === "sources" && (
        <div className="space-y-2">
          {sources.length === 0 && (
            <div className="text-gray-500 text-center py-8">No sources found</div>
          )}
          {sources.map((s) => (
            <a
              key={s.id}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block bg-[#111] border border-gray-800 rounded-lg p-3 hover:border-gray-600 transition-colors"
            >
              <div className="font-medium text-sm">{s.title}</div>
              <div className="flex gap-4 mt-1 text-xs text-gray-500">
                <span>{s.domain}</span>
                <span>{s.source_type}</span>
                <span>relevance: {(s.relevance_score * 100).toFixed(0)}%</span>
                <span>reliability: {(s.reliability_score * 100).toFixed(0)}%</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
