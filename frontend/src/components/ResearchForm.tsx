"use client";

import { useEffect, useRef, useState } from "react";

const SUGGESTIONS = [
  {
    title: "Cybersecurity & Generative AI",
    desc: "Examine prompt injection, model poisoning, and defense frameworks",
    query: "What are the main cybersecurity risks of generative AI?",
    icon: (
      <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: "Remote Work & Productivity",
    desc: "Empirical evidence from randomized firm experiments and macro surveys",
    query: "What evidence exists for the impact of remote work on productivity?",
    icon: (
      <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    title: "REST vs. GraphQL",
    desc: "Architecture tradeoffs, caching limitations, and performance at scale",
    query: "What are the tradeoffs between REST and GraphQL for large web applications?",
    icon: (
      <svg className="h-4 w-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: "RAG & Hallucination Mitigation",
    desc: "How grounding with retrieved documents reduces factual inaccuracy",
    query: "How does retrieval-augmented generation improve factual accuracy in LLMs?",
    icon: (
      <svg className="h-4 w-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
  },
];

const MIN_LENGTH = 10;
const MAX_LENGTH = 2000;

export default function ResearchForm({
  onSubmit,
  disabled,
  compact = false,
}: {
  onSubmit: (query: string) => void;
  disabled: boolean;
  compact?: boolean;
}) {
  const [query, setQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmed = query.trim();
  const canSubmit = trimmed.length >= MIN_LENGTH && query.length <= MAX_LENGTH && !disabled;

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, compact ? 120 : 200)}px`;
  }, [query, compact]);

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) {
        onSubmit(trimmed);
        setQuery("");
      }
    }
  }

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (canSubmit) {
      onSubmit(trimmed);
      setQuery("");
    }
  }

  if (compact) {
    return (
      <form onSubmit={handleFormSubmit} className="relative w-full">
        <div className="relative flex items-center rounded-2xl border border-zinc-300 bg-white shadow-md transition focus-within:border-zinc-500 focus-within:ring-2 focus-within:ring-zinc-900/10">
          <textarea
            ref={textareaRef}
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask a follow-up or a new research question…"
            className="max-h-32 min-h-[46px] w-full resize-none bg-transparent py-3 pl-4 pr-12 text-sm text-zinc-900 placeholder-zinc-400 outline-none"
          />
          <button
            type="submit"
            disabled={!canSubmit}
            aria-label="Send research request"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-full bg-zinc-900 p-2 text-white shadow transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-400"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 pt-4">
      {/* Hero Welcome (Gemini / Claude style) */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white/80 px-3.5 py-1 text-xs font-medium text-zinc-600 shadow-sm backdrop-blur">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          Autonomous Multi-Step AI Research Agent
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl">
          Where shall we research today?
        </h1>
        <p className="mx-auto max-w-xl text-sm leading-relaxed text-zinc-600">
          Plans targeted web searches, reads real live pages, synthesizes facts, and generates
          a comprehensive report with verifiable citations.
        </p>
      </div>

      {/* Main Prompt Input Box (ChatGPT / Claude style) */}
      <form onSubmit={handleFormSubmit} className="relative">
        <div className="overflow-hidden rounded-2xl border border-zinc-300 bg-white shadow-lg transition-all focus-within:border-zinc-600 focus-within:ring-4 focus-within:ring-zinc-900/5">
          <textarea
            ref={textareaRef}
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask any research question (e.g. What are the key tradeoffs between REST and GraphQL?)"
            className="w-full resize-none border-none bg-transparent px-5 pt-4 pb-2 text-[15px] leading-relaxed text-zinc-900 placeholder-zinc-400 outline-none"
          />

          <div className="flex items-center justify-between border-t border-zinc-100 px-4 py-2.5 bg-zinc-50/50">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <span className="inline-flex items-center gap-1 rounded-md bg-zinc-100 px-2 py-0.5 font-medium text-zinc-700">
                <svg className="h-3 w-3 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Tavily Search + Firecrawl Extraction
              </span>
            </div>

            <div className="flex items-center gap-3">
              {query.length >= MIN_LENGTH && (
                <span className="text-[11px] text-zinc-400">
                  {query.length} / {MAX_LENGTH}
                </span>
              )}
              <button
                type="submit"
                disabled={!canSubmit}
                aria-label="Start Research"
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 text-white shadow transition-all hover:bg-zinc-700 active:scale-95 disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-400"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <p className="mt-2 text-center text-[11px] text-zinc-400">
          Press <kbd className="rounded border border-zinc-200 bg-zinc-100 px-1 py-0.5 text-[10px] font-mono">Enter</kbd> to research · <kbd className="rounded border border-zinc-200 bg-zinc-100 px-1 py-0.5 text-[10px] font-mono">Shift+Enter</kbd> for new line
        </p>
      </form>

      {/* Suggested Topic Cards (Gemini / Claude style) */}
      <div className="space-y-2.5">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Suggested investigations
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {SUGGESTIONS.map((item) => (
            <button
              key={item.title}
              type="button"
              onClick={() => {
                setQuery(item.query);
                textareaRef.current?.focus();
              }}
              className="group flex items-start gap-3 rounded-xl border border-zinc-200/80 bg-white p-3.5 text-left shadow-sm transition hover:border-zinc-400 hover:shadow-md"
            >
              <div className="mt-0.5 rounded-lg bg-zinc-100 p-2 transition group-hover:bg-zinc-200/70">
                {item.icon}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-zinc-800 group-hover:text-zinc-950">
                  {item.title}
                </p>
                <p className="mt-0.5 line-clamp-1 text-xs text-zinc-500">
                  {item.desc}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
