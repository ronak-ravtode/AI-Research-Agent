import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Research Assistant",
  description: "Web research with cited sources.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
