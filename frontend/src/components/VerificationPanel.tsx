export default function VerificationPanel({
  note,
  revised,
  available,
  removedClaims,
}: {
  note: string | null;
  revised: boolean;
  available: boolean;
  removedClaims: number;
}) {
  if (!note && available && !revised) return null;

  const tone = !available
    ? {
        box: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/30",
        icon: "text-amber-600 dark:text-amber-400",
        title: "Verification unavailable",
        chip: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
      }
    : revised
      ? {
          box: "border-blue-200 bg-blue-50/60 dark:border-blue-900/50 dark:bg-blue-950/30",
          icon: "text-blue-600 dark:text-blue-400",
          title: "Claims checked and adjusted",
          chip: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
        }
      : {
          box: "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900/50 dark:bg-emerald-950/30",
          icon: "text-emerald-600 dark:text-emerald-400",
          title: "Claims checked against sources",
          chip: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
        };

  return (
    <div className={`flex items-start gap-3 rounded-xl border p-3.5 ${tone.box}`}>
      <span className={`mt-0.5 shrink-0 ${tone.icon}`}>
        {available ? (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.6-4A11.95 11.95 0 0112 2.94 11.95 11.95 0 013.4 6a12 12 0 00-.4 3c0 5.6 3.8 10.3 9 11.6 5.2-1.3 9-6 9-11.6 0-1-.13-2.05-.4-3z" />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" />
          </svg>
        )}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
            {tone.title}
          </p>
          {revised && removedClaims > 0 && (
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${tone.chip}`}>
              {removedClaims} claim{removedClaims === 1 ? "" : "s"} removed or qualified
            </span>
          )}
        </div>
        {note && (
          <p className="mt-1 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
            {note}
          </p>
        )}
      </div>
    </div>
  );
}
