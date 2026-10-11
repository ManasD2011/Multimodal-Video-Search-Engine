import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("API client", () => {
  it("returns library records from the backend", async () => {
    const records = [
      {
        video_id: "id-1",
        filename: "clip.mp4",
        duration_seconds: null,
        segment_count: 0,
        status: "uploaded" as const,
        added_at: "2025-01-01T00:00:00Z",
        size_bytes: 123,
        media_type: "video/mp4",
        media_url: "/videos/id-1/media",
      },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(records))));
    await expect(api.listVideos()).resolves.toEqual(records);
  });

  it("surfaces backend search-not-configured errors without hiding the status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Search index is not configured." }), {
          status: 503,
        }),
      ),
    );
    await expect(api.search("a red umbrella")).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      message: "Search index is not configured.",
    } satisfies Partial<ApiError>);
  });
});
