import { Film, Search, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ApiError,
  api,
  type SearchHit,
  type VideoRecord,
} from "@/api/client";
import { ResultsGrid } from "@/components/ResultsGrid";
import { SearchBar } from "@/components/SearchBar";
import { VideoPlayer } from "@/components/VideoPlayer";
import { Button } from "@/components/ui/button";

interface SearchPageProps {
  onOpenUpload: () => void;
  videoCount: number;
  videos: VideoRecord[];
}

export function SearchPage({
  onOpenUpload,
  videoCount,
  videos,
}: SearchPageProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectionKey, setSelectionKey] = useState(0);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  async function search(value: string) {
    setQuery(value);
    setBusy(true);
    setSearched(true);
    setError(null);
    setHits([]);
    setSelectedIndex(-1);
    const started = performance.now();
    try {
      const response = await api.search(value);
      setHits(response.hits);
      if (response.hits.length > 0) {
        setSelectedIndex(0);
        setSelectionKey((key) => key + 1);
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 503) {
        setError("Connect a retrieval index to search uploaded videos.");
      } else if (cause instanceof ApiError && cause.status === 0) {
        setError("Start the local API, then retry your search.");
      } else if (cause instanceof ApiError && cause.status === 422) {
        setError("Use a search query under 2,000 characters.");
      } else {
        setError("The search could not be completed. Retry in a moment.");
      }
    } finally {
      setLatencyMs(performance.now() - started);
      setBusy(false);
    }
  }

  useEffect(() => {
    function onKeyboardEvent(event: Event) {
      const key = (event as CustomEvent<string>).detail;
      if (key === "Enter") {
        if (hits.length === 0) return;
        setSelectedIndex((current) => {
          return current < 0 ? 0 : current;
        });
        setSelectionKey((selection) => selection + 1);
        return;
      }
      if (key !== "j" && key !== "k" && key !== "[" && key !== "]") return;
      if (hits.length === 0) return;
      const direction = key === "j" || key === "]" ? 1 : -1;
      setSelectedIndex((current) => {
        return current < 0
          ? 0
          : (current + direction + hits.length) % hits.length;
      });
      setSelectionKey((selection) => selection + 1);
    }
    window.addEventListener("vidsearch:key", onKeyboardEvent);
    return () => window.removeEventListener("vidsearch:key", onKeyboardEvent);
  }, [hits]);

  const selectedHit = selectedIndex >= 0 ? hits[selectedIndex] : undefined;
  const selectedVideo = selectedHit
    ? videos.find((video) => video.video_id === selectedHit.video_id)
    : undefined;
  const selectedVideoHits = selectedHit
    ? hits.filter((hit) => hit.video_id === selectedHit.video_id)
    : [];

  return (
    <main className="page-shell search-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">VIDSEARCH / SEARCH</p>
          <h1>Find a moment</h1>
        </div>
        <span className="library-count"><Film size={14} /> {videoCount} videos</span>
      </div>

      <SearchBar
        busy={busy}
        count={searched && !error ? hits.length : null}
        latencyMs={latencyMs}
        onSearch={(value) => void search(value)}
      />

      <div className="search-workspace">
        <section className="results-pane" aria-labelledby="results-heading">
          <div className="pane-heading">
            <div>
              <p className="eyebrow">MOMENTS</p>
              <h2 id="results-heading">
                {busy ? "Searching" : query ? "Search results" : "Results"}
              </h2>
            </div>
            {searched && !busy && !error && (
              <span className="result-count">{hits.length} matches</span>
            )}
          </div>
          <ResultsGrid
            busy={busy}
            error={error}
            hits={hits}
            onOpenLibrary={() => navigate("/library")}
            onSearch={(suggestion) => void search(suggestion)}
            onSelect={(index) => {
              setSelectedIndex(index);
              setSelectionKey((key) => key + 1);
            }}
            query={searched ? query : ""}
            selectedIndex={selectedIndex}
            videos={videos}
          />
          {error && (
            <div className="connection-notice">
              <XCircle aria-hidden="true" size={15} />
              <span>Search unavailable</span>
              <button onClick={() => void search(query)} type="button">Retry</button>
            </div>
          )}
        </section>

        <section className="review-pane" aria-label="Selected video preview">
          <div className="pane-heading review-heading">
            <div>
              <p className="eyebrow">REVIEW</p>
              <h2>{selectedHit ? "Selected moment" : "Player"}</h2>
            </div>
            {selectedHit && (
              <span className="result-count">
                {selectedVideoHits.length} {selectedVideoHits.length === 1 ? "match" : "matches"} in video
              </span>
            )}
          </div>
          {selectedHit && selectedVideo ? (
            <VideoPlayer
              endSeconds={selectedHit.end_seconds}
              key={`${selectedHit.video_id}-${selectedHit.start_seconds}-${selectionKey}`}
              matches={selectedVideoHits}
              startSeconds={selectedHit.start_seconds}
              video={selectedVideo}
            />
          ) : (
            <div className="player-empty">
              {error ? <XCircle size={18} /> : <Search size={18} />}
              <p>{error ? "Search is not connected" : "Select a result to review footage"}</p>
              <span>
                {error
                  ? "Your videos remain available in the library."
                  : "Video and timeline controls appear here."}
              </span>
              {error && (
                <Button onClick={onOpenUpload} size="sm" variant="secondary">
                  Add videos
                </Button>
              )}
            </div>
          )}
        </section>
      </div>

      {!searched && (
        <div className="search-footnote">
          <span><kbd>/</kbd> focus search</span>
          <span><kbd>j</kbd> <kbd>k</kbd> move through results</span>
          <span><kbd>⌘</kbd><kbd>K</kbd> commands</span>
        </div>
      )}
    </main>
  );
}
