import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Research Agent",
  description: "Test UI for the Agentic AI Research Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0a0a0a] text-[#ededed]">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <header className="mb-8 border-b border-gray-800 pb-4">
            <h1 className="text-2xl font-bold">AI Research Agent</h1>
            <p className="text-sm text-gray-400 mt-1">Test UI &mdash; submit a query, watch the pipeline, view results</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
