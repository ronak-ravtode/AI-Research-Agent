export type ResearchStatus = "queued" | "running" | "completed" | "failed";

export type Stage =
  | "queued"
  | "planning"
  | "searching"
  | "reading"
  | "deciding"
  | "writing"
  | "verifying"
  | "complete";

export interface StartResearchResponse {
  research_id: string;
  status: string;
}

export interface ResearchStatusResponse {
  research_id: string;
  query: string;
  status: ResearchStatus;
  current_stage: Stage | null;
  progress_message: string | null;
  error_message: string | null;
  planned_queries: string[] | null;
  parent_research_id: string | null;
  report_id: string | null;
  report_title: string | null;
  report_markdown: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface Source {
  id: string;
  title: string;
  url: string;
  domain: string | null;
  source_type: string;
  snippet: string | null;
  retrieval_method: "firecrawl" | "tavily_snippet";
  search_score: number;
  retrieved_at: string | null;
}

export interface SourceListResponse {
  sources: Source[];
  total: number;
}

export interface HistoryItem {
  research_id: string;
  query: string;
  status: ResearchStatus;
  source_count: number;
  has_report: boolean;
  parent_research_id: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface HistoryResponse {
  history: HistoryItem[];
}

export interface ActivityEvent {
  stage: Stage;
  message: string;
  at: string | null;
}

/** Terminal payload delivered on the SSE `complete` event. */
export interface CompleteEvent {
  research_id: string;
  status: ResearchStatus;
  current_stage: Stage | null;
  progress_message: string | null;
  message?: string;
}
