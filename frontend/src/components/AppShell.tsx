"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import CommandPalette from "@/components/CommandPalette";
import RecentResearch from "@/components/RecentResearch";
import ThemeToggle from "@/components/ThemeToggle";
import { getHealth } from "@/lib/api";
import { usePreferences } from "@/lib/preferences";
import type { HealthResponse } from "@/types/research";

function Logo() {
  return (
    <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 p-[1px] shadow-md shadow-indigo-500/25 ring-1 ring-white/20">
      <span className="flex h-full w-full items-center justify-center rounded-[11px] bg-gradient-to-br from-indigo-950 via-zinc-900 to-zinc-950">
        <svg className="h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
          <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-30 12 12)" stroke="url(#logo-orbit)" strokeWidth="1.25" strokeDasharray="3 1.5" />
          <path d="M12 4.5C12 7.8 8.8 11 5.5 11C8.8 11 12 14.2 12 17.5C12 14.2 15.2 11 18.5 11C15.2 11 12 7.8 12 4.5Z" fill="url(#logo-star)" />
          <circle cx="17.5" cy="8" r="1.25" fill="#38bdf8" />
          <defs>
            <linearGradient id="logo-star" x1="5.5" y1="4.5" x2="18.5" y2="17.5" gradientUnits="userSpaceOnUse">
              <stop stopColor="#60a5fa" />
              <stop offset="0.5" stopColor="#a855f7" />
              <stop offset="1" stopColor="#38bdf8" />
            </linearGradient>
            <linearGradient id="logo-orbit" x1="3" y1="8" x2="21" y2="16" gradientUnits="userSpaceOnUse">
              <stop stopColor="#818cf8" stopOpacity="0.8" />
              <stop offset="1" stopColor="#38bdf8" stopOpacity="0.3" />
            </linearGradient>
          </defs>
        </svg>
      </span>
    </span>
  );
}

function NavLink({
  href,
  active,
  icon,
  label,
  onClick,
}: {
  href: string;
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition ${
        active
          ? "bg-zinc-800 font-medium text-white"
          : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100"
      }`}
    >
      <span className={active ? "text-zinc-200" : "text-zinc-500"}>{icon}</span>
      {label}
    </Link>
  );
}

function pageTitle(pathname: string): string {
  if (pathname === "/") return "New research";
  if (pathname.startsWith("/library")) return "Library";
  if (pathname.startsWith("/settings")) return "Settings";
  if (/^\/r\/[^/]+\/sources\//.test(pathname)) return "Source";
  if (pathname.startsWith("/r/")) return "Research";
  return "AI Research Assistant";
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { preferences, setPreference } = usePreferences();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const activeId = pathname.match(/^\/r\/([^/]+)/)?.[1] ?? null;
  const desktopOpen = preferences.sidebarOpen;

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  // A new run changing the URL is the natural moment to refresh the recent list, so the
  // pathname itself is the refresh key rather than duplicated state.
  const closeMobile = () => setMobileOpen(false);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <aside
        className={[
          "fixed inset-y-0 left-0 z-40 flex h-full w-72 flex-col bg-[#18181b] text-zinc-100 transition-all duration-300 ease-in-out lg:static lg:z-auto",
          mobileOpen
            ? "translate-x-0 shadow-2xl lg:shadow-none"
            : "-translate-x-full",
          desktopOpen
            ? "lg:translate-x-0 lg:border-r lg:border-zinc-800/80 lg:p-3 lg:opacity-100"
            : "lg:w-0 lg:translate-x-0 lg:overflow-hidden lg:border-r-0 lg:p-0 lg:opacity-0 lg:pointer-events-none",
        ].join(" ")}
      >
        <div className="flex h-full w-[16.5rem] min-w-[16.5rem] flex-col overflow-hidden">
          <div className="mb-4 flex shrink-0 items-center justify-between px-2 pt-1">
            <Link href="/" onClick={closeMobile} className="flex items-center gap-2.5">
              <Logo />
              <span className="truncate">
                <span className="block truncate text-sm font-semibold tracking-tight text-white">
                  Research Agent
                </span>
                <span className="block truncate text-[11px] text-zinc-400">
                  Cited fact-checking
                </span>
              </span>
            </Link>

            <button
              type="button"
              onClick={() => {
                setMobileOpen(false);
                setPreference("sidebarOpen", !desktopOpen);
              }}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="rounded-lg p-1.5 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2" />
                <path d="M9 3v18" />
                <path d="m14 9-3 3 3 3" />
              </svg>
            </button>
          </div>

          <Link
            href="/"
            onClick={closeMobile}
            className="mb-3 flex items-center justify-between rounded-xl border border-zinc-700/60 bg-zinc-800/80 px-3.5 py-2.5 text-sm font-medium text-zinc-100 shadow-sm transition hover:border-zinc-500 hover:bg-zinc-700"
          >
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              New research
            </span>
            <span className="text-[11px] font-normal text-zinc-400">⌘K</span>
          </Link>

          <nav className="mb-3 space-y-0.5" aria-label="Main">
            <NavLink
              href="/library"
              active={pathname.startsWith("/library")}
              onClick={closeMobile}
              icon={
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 5h6v14H4zM14 5h6v14h-6z" />
                </svg>
              }
              label="All research"
            />
            <NavLink
              href="/settings"
              active={pathname.startsWith("/settings")}
              onClick={closeMobile}
              icon={
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <circle cx="12" cy="12" r="3" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.7 1.7 0 00.34 1.87l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.7 1.7 0 00-1.87-.34 1.7 1.7 0 00-1 1.55V21a2 2 0 11-4 0v-.09a1.7 1.7 0 00-1.11-1.55 1.7 1.7 0 00-1.87.34l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.7 1.7 0 004.6 15a1.7 1.7 0 00-1.55-1H3a2 2 0 110-4h.09A1.7 1.7 0 004.6 9a1.7 1.7 0 00-.34-1.87l-.06-.06a2 2 0 112.83-2.83l.06.06A1.7 1.7 0 009 4.6a1.7 1.7 0 001-1.55V3a2 2 0 114 0v.09a1.7 1.7 0 001 1.55 1.7 1.7 0 001.87-.34l.06-.06a2 2 0 112.83 2.83l-.06.06A1.7 1.7 0 0019.4 9v.09a1.7 1.7 0 001.55 1H21a2 2 0 110 4h-.09a1.7 1.7 0 00-1.55 1z" />
                </svg>
              }
              label="Settings"
            />
          </nav>

          <div className="flex min-h-0 flex-1 flex-col">
            <RecentResearch
              activeId={activeId}
              refreshKey={pathname}
              onNavigate={closeMobile}
            />
          </div>

          <div className="mt-auto border-t border-zinc-800/80 px-2 pt-3">
            <div className="flex items-center justify-between text-[11px] text-zinc-500">
              <span
                className="flex items-center gap-1.5"
                title={health ? `Model: ${health.providers.llm}` : undefined}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health?.configured === false ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                />
                {health
                  ? `${health.providers.search} + ${health.providers.extraction}`
                  : "Connecting…"}
              </span>
              <span>v{health?.version ?? "1.0.0"}</span>
            </div>
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={closeMobile}
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-xs lg:hidden"
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-zinc-200/80 bg-white/80 px-4 backdrop-blur-md sm:px-6 dark:border-zinc-800/80 dark:bg-zinc-950/80">
          <div className="flex min-w-0 items-center gap-2.5">
            <button
              type="button"
              onClick={() => {
                if (window.innerWidth < 1024) {
                  setMobileOpen(true);
                } else {
                  setPreference("sidebarOpen", !desktopOpen);
                }
              }}
              aria-label="Open sidebar"
              title="Open sidebar"
              className="focus-ring rounded-xl p-2 text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-white"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2" />
                <path d="M9 3v18" />
                <path d="m13 15 3-3-3-3" />
              </svg>
            </button>

            <span className="truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              {pageTitle(pathname)}
            </span>
            <span className="hidden items-center gap-1 rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-600 sm:inline-flex dark:bg-zinc-800 dark:text-zinc-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
              Live research model
            </span>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => {
                window.dispatchEvent(new Event("ara:palette"));
              }}
              aria-label="Open command palette"
              title="Search or run a command (⌘K)"
              className="focus-ring hidden items-center gap-2 rounded-lg border border-zinc-200 bg-white px-2.5 py-1.5 text-xs text-zinc-500 transition hover:border-zinc-300 hover:bg-zinc-50 sm:inline-flex dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-zinc-700 dark:hover:bg-zinc-800"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
              </svg>
              Search
              <kbd className="rounded border border-zinc-200 px-1 text-[10px] dark:border-zinc-700">⌘K</kbd>
            </button>
            <ThemeToggle />
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>

      <CommandPalette />
    </div>
  );
}
