"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import ResearchForm from "@/components/ResearchForm";
import { ApiError, startResearch } from "@/lib/api";
import { DEPTH_OPTIONS, usePreferences } from "@/lib/preferences";

export default function Home() {
  const router = useRouter();
  const { preferences } = usePreferences();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(question: string) {
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const { research_id } = await startResearch(question, {
        maxIterations: DEPTH_OPTIONS[preferences.depth].iterations,
      });
      // The run page owns the live state; the composer only needs the id.
      router.push(`/r/${research_id}`);
    } catch (cause) {
      setSubmitting(false);
      setError(
        cause instanceof ApiError ? cause.message : "Could not start research.",
      );
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-8 sm:py-16">
      <ResearchForm onSubmit={handleSubmit} disabled={submitting} />

      {error && (
        <div
          role="alert"
          className="mx-auto mt-6 max-w-3xl rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300"
        >
          {error}
        </div>
      )}

      <p className="mt-10 text-center text-[11px] text-zinc-400">
        Every run is saved to your library and can be shared by URL.
      </p>
    </div>
  );
}
