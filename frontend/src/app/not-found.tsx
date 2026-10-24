import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-white px-4 dark:bg-zinc-950">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          404
        </p>
        <h1 className="mt-3 text-2xl font-bold text-zinc-900 dark:text-zinc-50">
          Page not found
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          The page you asked for does not exist.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          Start a new research
        </Link>
      </div>
    </div>
  );
}
