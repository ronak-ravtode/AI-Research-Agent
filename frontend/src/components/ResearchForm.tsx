"use client";

import { useState } from "react";

const SAMPLE_QUESTIONS = [
  "What are the main cybersecurity risks of generative AI?",
  "How do retrieval-augmented generation systems work?",
  "What evidence exists for the impact of remote work on productivity?",
];

const MIN_LENGTH = 10;
const MAX_LENGTH = 2000;

export default function ResearchForm({
  onSubmit,
  disabled,
}: {
  onSubmit: (query: string) => void;
  disabled: boolean;
}) {
  const [query, setQuery] = useState("");
  const trimmed = query.trim();
  const tooShort = trimmed.length < MIN_LENGTH;
  const tooLong = query.length > MAX_LENGTH;
  const canSubmit = !tooShort && !tooLong && !disabled;

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter inserts a newline; only the explicit chord submits.
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      if (canSubmit) onSubmit(trimmed);
    }
  }

  return (
    <section aria-labelledby="ask-heading" className="space-y-4">
      <div>
        <h2 id="ask-heading" className="text-lg font-semibold text-stone-900">
          Ask a research question
        </h2>
        <p className="mt-1 text-sm text-stone-600">
          The assistant plans searches, reads real web pages, and answers with numbered
          citations you can open.
        </p>
      </div>

      <label htmlFor="research-question" className="sr-only">
        Research question
      </label>
      <textarea
        id="research-question"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={4}
        maxLength={MAX_LENGTH}
        disabled={disabled}
        placeholder="e.g. What are the main cybersecurity risks of generative AI?"
        className="w-full rounded-lg border border-stone-300 bg-white px-4 py-3 text-[15px] leading-relaxed text-stone-900 shadow-sm outline-none transition placeholder:text-stone-400 focus:border-stone-500 focus:ring-2 focus:ring-stone-900/10 disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-500"
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p
          className={`text-xs ${
            tooLong ? "text-red-700" : "text-stone-500"
          }`}
          aria-live="polite"
        >
          {trimmed.length < MIN_LENGTH
            ? `At least ${MIN_LENGTH} characters`
            : `${query.length} / ${MAX_LENGTH}`}
        </p>

        <button
          type="button"
          onClick={() => onSubmit(trimmed)}
          disabled={!canSubmit}
          className="rounded-lg bg-stone-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700 focus:outline-none focus:ring-2 focus:ring-stone-900/20 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-stone-300"
        >
          {disabled ? "Researching…" : "Start research"}
        </button>
      </div>

      <p className="text-xs text-stone-500">
        Press <kbd className="rounded border border-stone-300 bg-stone-50 px-1">Ctrl</kbd>{" "}
        + <kbd className="rounded border border-stone-300 bg-stone-50 px-1">Enter</kbd> to
        start.
      </p>

      {!disabled && (
        <div>
          <h3 className="text-xs font-semibold tracking-wide text-stone-500 uppercase">
            Try one of these
          </h3>
          <ul className="mt-2 flex flex-col gap-1.5">
            {SAMPLE_QUESTIONS.map((sample) => (
              <li key={sample}>
                <button
                  type="button"
                  onClick={() => setQuery(sample)}
                  className="w-full rounded-md border border-stone-200 bg-stone-50 px-3 py-2 text-left text-sm text-stone-700 transition hover:border-stone-400 hover:bg-white"
                >
                  {sample}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
