import type {
  ActivityEvent,
  CompleteEvent,
  HistoryResponse,
  ResearchStatusResponse,
  SourceListResponse,
  StartResearchResponse,
} from "@/types/research";

/**
 * All calls are same-origin and rely on the Next.js rewrite in next.config.ts to reach
 * FastAPI. Provider keys stay on the backend; nothing secret is ever read here.
 */
const BASE = "";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      cache: "no-store",
      ...init,
    });
  } catch {
    // A network-level failure has no status and no body; say so rather than pretending.
    throw new ApiError("Could not reach the server. Is the backend running?", 0);
  }

  if (!response.ok) {
    throw new ApiError(await readError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** Prefer the backend's own `detail` message over a bare status code. */
async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    // fall through to the generic message
  }
  return `Request failed (${response.status})`;
}

/** `parentResearchId` turns the request into a follow-up that reuses
 * the earlier run's memory (question, answer, best sources). */
export function startResearch(
  query: string,
  parentResearchId?: string,
): Promise<StartResearchResponse> {
  return request<StartResearchResponse>("/api/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      ...(parentResearchId ? { parent_research_id: parentResearchId } : {}),
    }),
  });
}

export function getResearchStatus(
  researchId: string,
): Promise<ResearchStatusResponse> {
  return request<ResearchStatusResponse>(
    `/api/research/${encodeURIComponent(researchId)}`,
  );
}

export function getSources(researchId: string): Promise<SourceListResponse> {
  return request<SourceListResponse>(
    `/api/research/${encodeURIComponent(researchId)}/sources`,
  );
}

export function getActivity(researchId: string): Promise<ActivityEvent[]> {
  return request<{ activity: ActivityEvent[] }>(
    `/api/research/${encodeURIComponent(researchId)}/activity`,
  ).then((body) => body.activity ?? []);
}

export function getHistory(): Promise<HistoryResponse> {
  return request<HistoryResponse>("/api/history");
}

export type StreamHandlers = {
  onStage: (event: ActivityEvent) => void;
  onComplete: (event: CompleteEvent) => void;
  onError: (message: string) => void;
  /** Transport trouble (not a failed run) — the caller should fall back to polling. */
  onDisconnected: () => void;
};

/**
 * Open the progress stream.
 *
 * `EventSource` reconnects on its own, but a mid-run failure must still be able to
 * surface, so the stream is closed by the caller on any terminal event.
 */
export function streamResearch(
  researchId: string,
  handlers: StreamHandlers,
): () => void {
  const url = `${BASE}/api/research/${encodeURIComponent(researchId)}/stream`;
  const source = new EventSource(url);

  const close = () => {
    source.close();
  };

  source.addEventListener("stage", (raw) => {
    const event = parse<ActivityEvent>(raw);
    if (event) handlers.onStage(event);
  });

  source.addEventListener("complete", (raw) => {
    const event = parse<CompleteEvent>(raw);
    if (event) {
      handlers.onComplete(event);
    } else {
      handlers.onError("The research stream ended unexpectedly.");
    }
    close();
  });

  source.addEventListener("error", (raw) => {
    const payload = parse<{ message?: string }>(raw);
    handlers.onError(payload?.message ?? "The research stream reported an error.");
    close();
  });

  source.addEventListener("timeout", () => {
    handlers.onDisconnected();
    close();
  });

  source.onerror = () => {
    // Native transport error: EventSource will retry, but the UI should say so and the
    // caller falls back to polling so progress is never silently frozen.
    handlers.onDisconnected();
  };

  return close;
}

function parse<T>(raw: Event): T | null {
  try {
    return JSON.parse((raw as MessageEvent).data) as T;
  } catch {
    // A malformed event is not worth tearing the stream down for.
    return null;
  }
}
