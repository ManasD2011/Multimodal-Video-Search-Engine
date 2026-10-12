import { AlertCircle, ArrowRight, Film, SearchX } from "lucide-react";
import type { VideoRecord, SearchHit } from "@/api/client";
import { VideoThumb } from "@/components/VideoThumb";
import { Button } from "@/components/ui/button";
import { formatTime } from "@/lib/utils";

interface ResultsGridProps {
  query: string;
  hits: SearchHit[];
  videos: VideoRecord[];
  selectedIndex: number;
  busy: boolean;
  error: string | null;
  onOpenLibrary: () => void;
  onSelect: (index: number) => void;
  onSearch: (query: string) => void;
}

export function ResultsGrid({
  query,
  hits,
  videos,
  selectedIndex,
  busy,
  error,
  onOpenLibrary,
  onSelect,
  onSearch,
}: ResultsGridProps) {
  if (busy) {
    return (
      <div className="result-skeletons" aria-label="Searching videos" aria-live="polite">
        {[0, 1, 2].map((item) => <div className="result-skeleton" key={item} />)}
      </div>
    );
  }
  if (error) {
    return (
      <div className="state-panel state-error" role="alert">
        <AlertCircle size={20} />
        <div>
          <p className="state-title">Video search is unavailable</p>
          <p>{error}</p>
          <p className="state-note">
            Check the video's indexing status in the library, then retry your
            search when indexing has completed.
          </p>
        </div>
      </div>
    );
  }
  if (!query) {
    return (
      <div className="state-panel compact-state">
        <Film size={18} />
        <p className="state-title">Search footage</p>
        <p>Describe what appears on screen or what is spoken.</p>
      </div>
    );
  }
  if (hits.length === 0) {
    return (
      <div className="state-panel compact-state">
        <SearchX size={18} />
        <p className="state-title">No matches for this query</p>
        <p>Try a visual description or a phrase from the video:</p>
        <div className="empty-suggestions">
          {["Ganpati idol", "a spoken phrase"].map((suggestion) => (
            <button key={suggestion} onClick={() => onSearch(suggestion)} type="button">{suggestion}</button>
          ))}
        </div>
        <Button className="empty-library-link" onClick={onOpenLibrary} variant="ghost">
          Browse library <ArrowRight size={13} />
        </Button>
      </div>
    );
  }
  const records = new Map(videos.map((video) => [video.video_id, video]));
  return (
    <div className="results-list" aria-label="Search results" role="listbox">
      {hits.map((hit, index) => {
        const video = records.get(hit.video_id);
        const evidence = hit.evidence
          .map((item) => item.text ?? (item.stream === "visual" ? "Visual match" : ""))
          .filter(Boolean)
          .join(", ");
        return (
          <button
            aria-selected={selectedIndex === index}
            className={`result-card ${selectedIndex === index ? "result-selected" : ""}`}
            key={`${hit.video_id}-${hit.start_seconds}`}
            onClick={() => onSelect(index)}
            role="option"
            type="button"
          >
            {video ? (
              <VideoThumb atSeconds={hit.start_seconds} video={video} />
            ) : (
              <span className="thumb-missing" aria-label="Video unavailable"><Film size={15} /></span>
            )}
            <span className="result-copy">
              <span className="result-name">{video?.filename ?? hit.video_id}</span>
              <span className="timecode result-timecode">
                {formatTime(hit.start_seconds)} – {formatTime(hit.end_seconds)}
              </span>
              <span className="result-evidence">{evidence || "Matched segment"}</span>
            </span>
            <span className="result-score">{Math.round(hit.score * 100)}%</span>
          </button>
        );
      })}
    </div>
  );
}
