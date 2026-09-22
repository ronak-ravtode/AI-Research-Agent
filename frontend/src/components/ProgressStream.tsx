"use client";

import { useEffect, useState, useRef } from "react";
import { streamResearch } from "@/lib/api";

interface Props {
  researchId: string;
  onStatusChange: (status: string) => void;
}

interface LogEntry {
  event: string;
  status: string;
  time: string;
}

const STATUS_LABELS: Record<string, string> = {
  planning: "Planning research...",
  researching: "Searching the web...",
  extracting: "Extracting evidence...",
  verifying: "Verifying claims...",
  analyzing: "Analyzing findings...",
  writing: "Generating report...",
  completed: "Research complete!",
  failed: "Research failed",
};

export default function ProgressStream({ researchId, onStatusChange }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentStatus, setCurrentStatus] = useState("planning");
  const [done, setDone] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const es = streamResearch(researchId);
    const startTime = Date.now();

    es.addEventListener("status", (e) => {
      try {
        const data = JSON.parse(e.data);
        const status = data.status;
        setCurrentStatus(status);
        onStatusChange(status);

        setLogs((prev) => [
          ...prev,
          {
            event: "status",
            status,
            time: `${((Date.now() - startTime) / 1000).toFixed(1)}s`,
          },
        ]);
      } catch {}
    });

    es.addEventListener("complete", (e) => {
      try {
        const data = JSON.parse(e.data);
        setCurrentStatus(data.status);
        onStatusChange(data.status);
        setDone(true);
        setLogs((prev) => [
          ...prev,
          {
            event: "complete",
            status: data.status,
            time: `${((Date.now() - startTime) / 1000).toFixed(1)}s`,
          },
        ]);
      } catch {}
      es.close();
    });

    es.addEventListener("error", () => {
      setDone(true);
      es.close();
    });

    return () => es.close();
  }, [researchId, onStatusChange]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${done ? (currentStatus === "completed" ? "bg-green-500" : "bg-red-500") : "bg-blue-500 animate-pulse"}`} />
        <span className="font-medium">
          {STATUS_LABELS[currentStatus] || currentStatus}
        </span>
      </div>

      <div className="bg-[#111] border border-gray-800 rounded-lg p-3 max-h-60 overflow-y-auto font-mono text-xs">
        {logs.map((log, i) => (
          <div key={i} className="flex gap-3 py-0.5">
            <span className="text-gray-500 w-16 shrink-0">{log.time}</span>
            <span className={log.status === "completed" ? "text-green-400" : log.status === "failed" ? "text-red-400" : "text-gray-300"}>
              {STATUS_LABELS[log.status] || log.status}
            </span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
