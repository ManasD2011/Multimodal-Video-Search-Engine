export interface VideoRecord {
  video_id: string;
  filename: string;
  duration_seconds: number | null;
  segment_count: number;
  status: "uploaded" | "indexing" | "ready" | "failed";
  processing_error?: string | null;
  added_at: string;
  size_bytes: number;
  media_type: string;
  media_url: string;
}

export interface SearchHit {
  video_id: string;
  start_seconds: number;
  end_seconds: number;
  score: number;
  evidence: { stream: string; text: string | null }[];
}

export interface SearchResponse {
  query: string;
  total: number;
  sources: string[];
  hits: SearchHit[];
}

export interface HealthResponse {
  status: string;
  search_ready: boolean;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(
      "Cannot reach the Vidsearch API. Start the backend and try again.",
      0,
    );
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") message = payload.detail;
    } catch {
      // Keep the status-based error when the API did not return JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/healthz"),
  listVideos: () => request<VideoRecord[]>("/videos"),
  uploadVideo: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<VideoRecord>("/ingest/upload", { method: "POST", body });
  },
  importVideoUrl: (url: string) =>
    request<VideoRecord>("/ingest/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
  deleteVideo: (videoId: string) =>
    request<void>(`/videos/${encodeURIComponent(videoId)}`, {
      method: "DELETE",
    }),
  search: (query: string, topK = 20) =>
    request<SearchResponse>("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK }),
    }),
};

export function resolveMediaUrl(mediaUrl: string): string {
  return `${API_BASE_URL}${mediaUrl}`;
}
