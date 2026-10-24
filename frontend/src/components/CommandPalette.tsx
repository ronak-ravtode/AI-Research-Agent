"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { getHistory } from "@/lib/api";
import { formatRelativeDate } from "@/lib/format";
import { usePreferences } from "@/lib/preferences";
import type { HistoryItem } from "@/types/research";

interface Command {
  id: string;
  label: string;
  hint?: string;
  group: "Actions" | "Research";
  icon: ReactNode;
  run: () => void;
}

const ICONS = {
  plus: (
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
  ),
  library: (
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 5h6v14H4zM14 5h6v14h-6z" />
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.4 15a1.7 1.7 0 00.34 1.87l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.7 1.7 0 00-1.87-.34 1.7 1.7 0 00-1 1.55V21a2 2 0 11-4 0v-.09a1.7 1.7 0 00-1.11-1.55 1.7 1.7 0 00-1.87.34l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.7 1.7 0 004.6 15a1.7 1.7 0 00-1.55-1H3a2 2 0 110-4h.09A1.7 1.7 0 004.6 9a1.7 1.7 0 00-.34-1.87l-.06-.06a2 2 0 112.83-2.83l.06.06A1.7 1.7 0 009 4.6a1.7 1.7 0 001-1.55V3a2 2 0 114 0v.09a1.7 1.7 0 001 1.55 1.7 1.7 0 001.87-.34l.06-.06a2 2 0 112.83 2.83l-.06.06A1.7 1.7 0 0019.4 9v.09a1.7 1.7 0 001.55 1H21a2 2 0 110 4h-.09a1.7 1.7 0 00-1.55 1z"
      />
    </>
  ),
  theme: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
    />
  ),
  link: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M10 13a5 5 0 007.07 0l1.41-1.41a5 5 0 00-7.07-7.07L10 5.93M14 11a5 5 0 00-7.07 0L5.5 12.41a5 5 0 007.07 7.07L14 18.07"
    />
  ),
  doc: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
    />
  ),
};

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      className="h-4 w-4 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.8}
    >
      {children}
    </svg>
  );
}

export default function CommandPalette() {
  const router = useRouter();
  const { resolvedTheme, setPreference } = usePreferences();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((prev) => !prev);
        return;
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    const onOpenEvent = () => setOpen(true);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("ara:palette", onOpenEvent);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("ara:palette", onOpenEvent);
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const frame = requestAnimationFrame(() => {
      setActive(0);
      inputRef.current?.focus();
    });
    getHistory({ limit: 6 })
      .then((body) => setItems(body.history ?? []))
      .catch(() => setItems([]));
    return () => cancelAnimationFrame(frame);
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const actions: Command[] = [
      {
        id: "new",
        label: "New research",
        hint: "Start a fresh question",
        group: "Actions",
        icon: <Icon>{ICONS.plus}</Icon>,
        run: () => router.push("/"),
      },
      {
        id: "library",
        label: "All research",
        hint: "Browse, rename, delete",
        group: "Actions",
        icon: <Icon>{ICONS.library}</Icon>,
        run: () => router.push("/library"),
      },
      {
        id: "settings",
        label: "Settings",
        hint: "Theme and research depth",
        group: "Actions",
        icon: <Icon>{ICONS.settings}</Icon>,
        run: () => router.push("/settings"),
      },
      {
        id: "theme",
        label: resolvedTheme === "dark" ? "Switch to light theme" : "Switch to dark theme",
        group: "Actions",
        icon: <Icon>{ICONS.theme}</Icon>,
        run: () => setPreference("theme", resolvedTheme === "dark" ? "light" : "dark"),
      },
      {
        id: "copy",
        label: "Copy link to this page",
        group: "Actions",
        icon: <Icon>{ICONS.link}</Icon>,
        run: () => {
          void navigator.clipboard?.writeText(window.location.href);
        },
      },
    ];

    const research: Command[] = items.map((item) => ({
      id: item.research_id,
      label: item.title || item.query,
      hint: [item.status, item.source_count ? `${item.source_count} sources` : null, formatRelativeDate(item.created_at)]
        .filter(Boolean)
        .join(" · "),
      group: "Research",
      icon: <Icon>{ICONS.doc}</Icon>,
      run: () => router.push(`/r/${item.research_id}`),
    }));

    return [...actions, ...research];
  }, [items, resolvedTheme, router, setPreference]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return commands;
    return commands.filter(
      (command) =>
        command.label.toLowerCase().includes(needle) ||
        command.hint?.toLowerCase().includes(needle),
    );
  }, [commands, query]);

  // Clamp to the current result set without a state-syncing effect: if the highlight is
  // past the end (because the query narrowed the list), fall back to the first row.
  const activeIndex = active < filtered.length ? active : 0;

  function choose(command: Command) {
    close();
    command.run();
  }

  function onInputKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((prev) => (filtered.length ? (prev + 1) % filtered.length : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((prev) =>
        filtered.length ? (prev - 1 + filtered.length) % filtered.length : 0,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      const command = filtered[activeIndex];
      if (command) choose(command);
    }
  }

  if (!open) return null;

  let lastGroup = "";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center bg-zinc-950/40 px-4 pt-[12vh] backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className="w-full max-w-xl overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900"
      >
        <div className="flex items-center gap-2.5 border-b border-zinc-100 px-4 dark:border-zinc-800">
          <svg className="h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Search research or run a command…"
            aria-label="Search research or run a command"
            className="h-12 w-full bg-transparent text-sm text-zinc-900 outline-none placeholder-zinc-400 dark:text-zinc-100"
          />
          <kbd className="hidden shrink-0 rounded border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-[10px] text-zinc-500 sm:block dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
            Esc
          </kbd>
        </div>

        <div className="max-h-[min(60vh,26rem)] overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <p className="px-3 py-8 text-center text-sm text-zinc-500">
              No matches for “{query}”.
            </p>
          ) : (
            <ul role="listbox" aria-label="Commands">
              {filtered.map((command, index) => {
                const showGroup = command.group !== lastGroup;
                lastGroup = command.group;
                return (
                  <li key={`${command.group}-${command.id}`}>
                    {showGroup && (
                      <p className="px-2 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                        {command.group}
                      </p>
                    )}
                    <button
                      type="button"
                      role="option"
                      aria-selected={index === activeIndex}
                      onMouseEnter={() => setActive(index)}
                      onClick={() => choose(command)}
                      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left transition ${
                        index === activeIndex
                          ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-white"
                          : "text-zinc-600 dark:text-zinc-300"
                      }`}
                    >
                      <span className="text-zinc-400 dark:text-zinc-500">
                        {command.icon}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm">{command.label}</span>
                        {command.hint && (
                          <span className="block truncate text-[11px] text-zinc-400">
                            {command.hint}
                          </span>
                        )}
                      </span>
                      {index === activeIndex && (
                        <kbd className="shrink-0 rounded border border-zinc-300 px-1.5 py-0.5 text-[10px] text-zinc-500 dark:border-zinc-600 dark:text-zinc-400">
                          ↵
                        </kbd>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-zinc-100 px-4 py-2 text-[11px] text-zinc-400 dark:border-zinc-800">
          <span>↑↓ to navigate · ↵ to open</span>
          <span>⌘K</span>
        </div>
      </div>
    </div>
  );
}
