"use client";

import { useEffect, useState } from "react";

import { DepthPicker } from "@/components/ResearchForm";
import { getHealth } from "@/lib/api";
import {
  DEPTH_OPTIONS,
  usePreferences,
  type Theme,
} from "@/lib/preferences";
import type { HealthResponse } from "@/types/research";

const THEMES: { value: Theme; label: string; description: string }[] = [
  { value: "light", label: "Light", description: "Always light." },
  { value: "dark", label: "Dark", description: "Always dark." },
  { value: "system", label: "System", description: "Follow your OS setting." },
];

const DEPTHS: Array<"quick" | "standard" | "deep"> = [
  "quick",
  "standard",
  "deep",
];

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-b border-zinc-200/80 py-7 first:pt-0 last:border-b-0 dark:border-zinc-800">
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h2>
      <p className="mt-1 text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
        {description}
      </p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition ${
        checked ? "bg-blue-600" : "bg-zinc-300 dark:bg-zinc-700"
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

export default function SettingsPanel() {
  const { preferences, setPreference, reset, resolvedTheme } = usePreferences();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealthError(true));
  }, []);

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-8">
      <h1 className="text-2xl font-bold tracking-tight text-zinc-950 dark:text-zinc-50">
        Settings
      </h1>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
        Preferences are stored in this browser. Research depth is sent with each new
        run.
      </p>

      <div className="mt-8">
        <Section
          title="Appearance"
          description={`Currently showing the ${resolvedTheme} theme.`}
        >
          <div className="grid gap-2 sm:grid-cols-3">
            {THEMES.map((theme) => {
              const active = preferences.theme === theme.value;
              return (
                <button
                  key={theme.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setPreference("theme", theme.value)}
                  className={`rounded-xl border p-3 text-left transition ${
                    active
                      ? "border-blue-500 bg-blue-50/60 ring-1 ring-blue-500/40 dark:border-blue-500 dark:bg-blue-950/30"
                      : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
                  }`}
                >
                  <span className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-800 dark:text-zinc-100">
                      {theme.label}
                    </span>
                    {active && (
                      <svg className="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </span>
                  <span className="mt-1 block text-[11px] text-zinc-500 dark:text-zinc-400">
                    {theme.description}
                  </span>
                </button>
              );
            })}
          </div>
        </Section>

        <Section
          title="Research depth"
          description="How many evidence-gap follow-up rounds the agent may run. Deeper runs cost more and take longer, but cover more ground."
        >
          <div className="grid gap-2 sm:grid-cols-3">
            {DEPTHS.map((depth) => {
              const active = preferences.depth === depth;
              const option = DEPTH_OPTIONS[depth];
              return (
                <button
                  key={depth}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setPreference("depth", depth)}
                  className={`rounded-xl border p-3 text-left transition ${
                    active
                      ? "border-blue-500 bg-blue-50/60 ring-1 ring-blue-500/40 dark:border-blue-500 dark:bg-blue-950/30"
                      : "border-zinc-200 bg-white hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
                  }`}
                >
                  <span className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-800 dark:text-zinc-100">
                      {option.label}
                    </span>
                    <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-medium text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                      {option.iterations === 0
                        ? "no follow-ups"
                        : `${option.iterations} round${option.iterations === 1 ? "" : "s"}`}
                    </span>
                  </span>
                  <span className="mt-1 block text-[11px] leading-relaxed text-zinc-500 dark:text-zinc-400">
                    {option.description}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="mt-3 flex items-center gap-2 text-[11px] text-zinc-400">
            <span>Quick switch:</span>
            <DepthPicker
              value={preferences.depth}
              onChange={(depth) => setPreference("depth", depth)}
              size="small"
            />
          </div>
        </Section>

        <Section
          title="Reading"
          description="How reports present their evidence."
        >
          <div className="flex items-center justify-between gap-4 rounded-xl border border-zinc-200 bg-white p-3.5 dark:border-zinc-800 dark:bg-zinc-900">
            <div>
              <p className="text-sm font-medium text-zinc-800 dark:text-zinc-100">
                Citation previews
              </p>
              <p className="mt-0.5 text-[11px] leading-relaxed text-zinc-500 dark:text-zinc-400">
                Show the cited page&apos;s title and snippet when hovering a [n] badge.
              </p>
            </div>
            <Switch
              checked={preferences.citationPreview}
              onChange={(value) => setPreference("citationPreview", value)}
              label="Citation previews"
            />
          </div>
        </Section>

        <Section
          title="Runtime"
          description="What this deployment is actually using. Read-only; configured by the backend environment."
        >
          {healthError ? (
            <p className="text-xs text-red-600 dark:text-red-400">
              Could not reach the backend. Is it running?
            </p>
          ) : !health ? (
            <div className="h-20 animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-900" />
          ) : (
            <dl className="divide-y divide-zinc-100 overflow-hidden rounded-xl border border-zinc-200 bg-white text-sm dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
              {[
                ["Model", health.providers.llm],
                ["Search", health.providers.search],
                ["Extraction", health.providers.extraction],
                ["Search results per query", String(health.limits.max_search_results)],
                ["Sources read per run", String(health.limits.max_extract_sources)],
                ["Server default depth", `${health.limits.max_agent_iterations} follow-up rounds`],
                ["Environment", `${health.environment} · v${health.version}`],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between gap-4 px-3.5 py-2.5"
                >
                  <dt className="text-xs text-zinc-500 dark:text-zinc-400">{label}</dt>
                  <dd className="truncate text-right text-xs font-medium text-zinc-800 dark:text-zinc-200">
                    {value}
                  </dd>
                </div>
              ))}
              <div className="flex items-center justify-between gap-4 px-3.5 py-2.5">
                <dt className="text-xs text-zinc-500 dark:text-zinc-400">
                  Provider keys
                </dt>
                <dd
                  className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                    health.configured
                      ? "text-emerald-700 dark:text-emerald-400"
                      : "text-amber-700 dark:text-amber-400"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      health.configured ? "bg-emerald-500" : "bg-amber-500"
                    }`}
                  />
                  {health.configured ? "Configured" : "Missing keys"}
                </dd>
              </div>
            </dl>
          )}
        </Section>

        <Section
          title="Local data"
          description="Theme, depth, and reading preferences live in this browser only. Research itself stays on the server."
        >
          <button
            type="button"
            onClick={() => {
              if (window.confirm("Reset all preferences on this device?")) reset();
            }}
            className="rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs font-medium text-zinc-700 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:border-red-800 dark:hover:bg-red-950/30 dark:hover:text-red-300"
          >
            Reset preferences
          </button>
        </Section>
      </div>
    </div>
  );
}
