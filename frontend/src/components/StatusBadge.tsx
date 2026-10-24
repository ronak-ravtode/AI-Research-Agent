import type { ResearchStatus } from "@/types/research";

const STYLES: Record<ResearchStatus, { dot: string; chip: string }> = {
  queued: {
    dot: "bg-amber-400",
    chip: "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-500/30",
  },
  running: {
    dot: "bg-blue-500 animate-pulse",
    chip: "bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-950/40 dark:text-blue-300 dark:ring-blue-500/30",
  },
  completed: {
    dot: "bg-emerald-500",
    chip: "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-500/30",
  },
  failed: {
    dot: "bg-red-500",
    chip: "bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950/40 dark:text-red-300 dark:ring-red-500/30",
  },
  cancelled: {
    dot: "bg-zinc-400",
    chip: "bg-zinc-100 text-zinc-600 ring-zinc-500/20 dark:bg-zinc-800 dark:text-zinc-300 dark:ring-zinc-600/40",
  },
};

/**
 * Resolve a style for whatever status the API actually returned.
 *
 * The types say `ResearchStatus`, but history can carry rows written by an older schema
 * (for example a stage name like "planning" left behind by a crashed run). Indexing
 * `STYLES` with an unexpected value would crash the whole page, so anything unknown falls
 * back to the neutral `queued` look instead.
 */
function styleFor(status: string): { dot: string; chip: string } {
  return STYLES[status as ResearchStatus] ?? STYLES.queued;
}

export function StatusDot({ status }: { status: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${styleFor(status).dot}`}
    />
  );
}

export function StatusLabel({ status }: { status: string }) {
  if (status === "running") return <>Researching</>;
  return <span className="capitalize">{status}</span>;
}

export default function StatusBadge({
  status,
  className = "",
}: {
  status: string;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ring-inset ${styleFor(status).chip} ${className}`}
    >
      <StatusDot status={status} />
      <StatusLabel status={status} />
    </span>
  );
}
