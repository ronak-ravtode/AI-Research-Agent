const API_BASE = "";

export interface ResearchSession {
  research_id: string;
  query: string;
  status: string;
  research_depth: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface Report {
  id: string;
  research_id: string;
  title: string;
  content: string;
  created_at: string | null;
}

export interface Source {
  id: string;
  title: string;
  url: string;
  domain: string | null;
  source_type: string | null;
  relevance_score: number;
  reliability_score: number;
}

export interface HistoryItem {
  research_id: string;
  query: string;
  status: string;
  research_depth: string;
  created_at: string | null;
}

export async function startResearch(query: string, depth: string = "standard") {
  const res = await fetch(`${API_BASE}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, depth }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<{ research_id: string; status: string }>;
}

export async function getResearchStatus(researchId: string) {
  const res = await fetch(`${API_BASE}/api/research/${researchId}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<ResearchSession>;
}

export async function getReport(researchId: string) {
  const res = await fetch(`${API_BASE}/api/research/${researchId}/report`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<Report>;
}

export async function getSources(researchId: string) {
  const res = await fetch(`${API_BASE}/api/research/${researchId}/sources`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<{ sources: Source[]; total: number }>;
}

export async function getHistory() {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<{ history: HistoryItem[] }>;
}

export function streamResearch(researchId: string) {
  return new EventSource(`${API_BASE}/api/research/${researchId}/stream`);
}
