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
          <p className="state-title">Search index is not connected</p>
          <p>{error}</p>
          <p className="state-note">
            The library and local playback work now; matches will appear once a
            retrieval index is connected.
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
        <p>Describe a moment to find a timestamp.</p>
      </div>
    );
  }
  if (hits.length === 0) {
    return (
      <div className="state-panel compact-state">
        <SearchX size={18} />
        <p className="state-title">No matches for this query</p>
        <p>Try a broader description or search for:</p>
        <div className="empty-suggestions">
          {["person walking", "a spoken phrase"].map((suggestion) => (
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
        const evidence = hit.evidence.map((item) => item.text).filter(Boolean).join(", ");
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
