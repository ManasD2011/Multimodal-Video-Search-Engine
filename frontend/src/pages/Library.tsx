import { ArrowDown, ArrowUp, Film, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { api, type VideoRecord } from "@/api/client";
import { VideoPlayer } from "@/components/VideoPlayer";
import { VideoThumb } from "@/components/VideoThumb";
import { Button } from "@/components/ui/button";
import { formatBytes, formatTime } from "@/lib/utils";

interface LibraryPageProps {
  videos: VideoRecord[];
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
  onOpenUpload: () => void;
}

type SortMode = "newest" | "name";

export function LibraryPage({
  videos,
  loading,
  error,
  onRefresh,
  onOpenUpload,
}: LibraryPageProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "indexed" | "not-indexed">("all");
  const [sort, setSort] = useState<SortMode>("newest");
  const [actionError, setActionError] = useState<string | null>(null);
  const selected = videos.find((video) => video.video_id === selectedId) ?? null;
  const visibleVideos = useMemo(() => {
    const filtered = videos.filter((video) => {
      if (filter === "indexed") return video.status === "ready";
      if (filter === "not-indexed") return video.status !== "ready";
      return true;
    });
    return filtered.sort((first, second) => sort === "name"
      ? first.filename.localeCompare(second.filename)
      : second.added_at.localeCompare(first.added_at));
  }, [filter, sort, videos]);

  async function remove(video: VideoRecord) {
    if (!window.confirm(`Delete ${video.filename}?`)) return;
    setActionError(null);
    try {
      await api.deleteVideo(video.video_id);
      if (selectedId === video.video_id) setSelectedId(null);
      await onRefresh();
    } catch (cause) {
      setActionError(cause instanceof Error
        ? "The video could not be deleted. Retry the action."
        : "The video could not be deleted. Retry the action.");
    }
  }

  return (
    <main className="page-shell library-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">VIDSEARCH / LIBRARY</p>
          <h1>Video library</h1>
        </div>
        <Button onClick={onOpenUpload} size="sm" variant="default">
          Add videos
        </Button>
      </div>

      {selected && <VideoPlayer key={selected.video_id} video={selected} />}

      <div className="library-toolbar">
        <div className="library-tabs" aria-label="Filter videos">
          {([
            ["all", "All videos"],
            ["not-indexed", "Not indexed"],
            ["indexed", "Indexed"],
          ] as const).map(([value, label]) => (
            <button
              aria-pressed={filter === value}
              className={`library-tab ${filter === value ? "active" : ""}`}
              key={value}
              onClick={() => setFilter(value)}
              type="button"
            >
              {label}
              <span>{value === "all"
                ? videos.length
                : value === "indexed"
                  ? videos.filter((video) => video.status === "ready").length
                  : videos.filter((video) => video.status !== "ready").length}</span>
            </button>
          ))}
        </div>
        <button
          aria-label={`Sort by ${sort === "newest" ? "name" : "newest"}`}
          className="sort-label"
          onClick={() => setSort((current) => current === "newest" ? "name" : "newest")}
          type="button"
        >
          {sort === "newest" ? <ArrowDown size={13} /> : <ArrowUp size={13} />}
          {sort === "newest" ? "Recently added" : "Name"}
        </button>
      </div>

      {error && <p className="inline-error" role="alert">{error}</p>}
      {actionError && <p className="inline-error" role="alert">{actionError}</p>}
      {loading ? (
        <div className="table-skeletons" aria-label="Loading videos">
          {[0, 1, 2].map((item) => <div className="table-skeleton" key={item} />)}
        </div>
      ) : visibleVideos.length === 0 ? (
        <div className="library-empty">
          <Film size={19} />
          <p className="state-title">
            {filter === "indexed" ? "No indexed videos" : "Add your first video"}
          </p>
          <p>
            Local uploads can be previewed now. Search indexing is not connected yet.
          </p>
          {filter !== "indexed" && (
            <Button onClick={onOpenUpload} size="sm">Add videos</Button>
          )}
        </div>
      ) : (
        <div className="library-table-scroll">
          <table className="library-table">
            <thead>
              <tr>
                <th scope="col" className="preview-column">Frame</th>
                <th scope="col">Name</th>
                <th scope="col">Duration</th>
                <th scope="col">Segments</th>
                <th scope="col">Status</th>
                <th scope="col">Added</th>
                <th scope="col"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {visibleVideos.map((video) => (
                <tr className={selectedId === video.video_id ? "selected-row" : ""} key={video.video_id}>
                  <td className="preview-column">
                    <button
                      aria-label={`Preview ${video.filename}`}
                      className="thumb-button"
                      onClick={() => setSelectedId(video.video_id)}
                      type="button"
                    >
                      <VideoThumb video={video} />
                    </button>
                  </td>
                  <td>
                    <button
                      className="file-name"
                      onClick={() => setSelectedId(video.video_id)}
                      type="button"
                    >
                      {video.filename}
                    </button>
                    <span className="file-size">{formatBytes(video.size_bytes)}</span>
                  </td>
                  <td className="data-cell">{video.duration_seconds === null ? "—" : formatTime(video.duration_seconds)}</td>
                  <td className="data-cell">{video.segment_count || "—"}</td>
                  <td>
                    <span className={`status-tag status-${video.status}`}>
                      <span aria-hidden="true" />
                      {video.status === "ready" ? "Indexed" : "Not indexed"}
                    </span>
                  </td>
                  <td className="date-cell">{new Date(video.added_at).toLocaleDateString()}</td>
                  <td>
                    <Button
                      aria-label={`Delete ${video.filename}`}
                      onClick={() => void remove(video)}
                      size="icon"
                      variant="ghost"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
