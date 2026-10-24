"use client";

import { useEffect } from "react";

/**
 * Route-level error boundary. Catches render/data errors below the root layout so a
 * single broken page does not blank the whole app, and offers a non-destructive retry.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface it in the browser console; there is no client-side error sink here.
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4 py-16">
      <div className="w-full max-w-md text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Something went wrong
        </p>
        <h1 className="mt-3 text-2xl font-bold text-zinc-900 dark:text-zinc-50">
          This page could not be shown
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">
          The error was reported to the console. You can try again without losing your
          place.
        </p>
        <button
          type="button"
          onClick={reset}
          className="focus-ring mt-6 inline-flex rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
