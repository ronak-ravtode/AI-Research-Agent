import type { Metadata } from "next";

import { PreferencesProvider } from "@/lib/preferences";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Research Assistant",
  description: "Web research with cited sources.",
};

/**
 * Runs before first paint so the saved theme is applied without a flash of light.
 *
 * It is rendered as a plain server-side `<script>` (not `next/script`, which is a
 * client component): React 19 warns when a client component renders a `<script>`,
 * because that script sits outside the main document and React cannot guarantee it
 * runs. A server-rendered script is emitted into the HTML and executed by the parser
 * before the body paints, so it stays flash-free and warning-free.
 *
 * Kept tiny and dependency-free on purpose.
 */
const THEME_SCRIPT = `(function(){try{var p=JSON.parse(localStorage.getItem("ara.prefs.v1")||"{}");var t=p.theme||"system";var d=t==="dark"||(t==="system"&&window.matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.toggle("dark",d);document.documentElement.style.colorScheme=d?"dark":"light";}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          id="theme-init"
          suppressHydrationWarning
          dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }}
        />
      </head>
      <body className="min-h-screen antialiased" suppressHydrationWarning>
        <PreferencesProvider>{children}</PreferencesProvider>
      </body>
    </html>
  );
}
