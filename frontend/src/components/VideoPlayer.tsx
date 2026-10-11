import { Maximize2, Pause, Play, RotateCcw, RotateCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { resolveMediaUrl, type SearchHit, type VideoRecord } from "@/api/client";
import { Timeline, type TimelineHit } from "@/components/Timeline";
import { Button } from "@/components/ui/button";

interface VideoPlayerProps {
  video: VideoRecord;
  startSeconds?: number;
  endSeconds?: number;
  matches?: SearchHit[];
}

export function VideoPlayer({
  video,
  startSeconds,
  endSeconds,
  matches = [],
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  const timelineHits: TimelineHit[] = matches.map((hit) => ({
    start: hit.start_seconds,
    end: hit.end_seconds,
    score: hit.score,
  }));

  useEffect(() => {
    const player = videoRef.current;
    if (!player || startSeconds === undefined) return;
    const targetSeconds = startSeconds;
    function startAtMatch() {
      if (!player) return;
      player.currentTime = Math.max(0, targetSeconds - 2);
      player.play().then(
        () => setPlaying(true),
        () => setPlaybackError("Playback could not start. Use the player controls to retry."),
      );
    }
    if (player.readyState >= HTMLMediaElement.HAVE_METADATA) startAtMatch();
    else player.addEventListener("loadedmetadata", startAtMatch, { once: true });
    return () => player.removeEventListener("loadedmetadata", startAtMatch);
  }, [startSeconds, video.video_id]);

  const seek = useCallback((seconds: number) => {
    const player = videoRef.current;
    if (player && Number.isFinite(player.duration)) {
      player.currentTime = Math.max(0, Math.min(player.duration, seconds));
    }
  }, []);
  const togglePlayback = useCallback(() => {
    const player = videoRef.current;
    if (!player) return;
    if (player.paused) {
      player.play().then(
        () => {
          setPlaying(true);
          setPlaybackError(null);
        },
        () => setPlaybackError("Playback could not start. Try another video format."),
      );
    } else {
      player.pause();
      setPlaying(false);
    }
  }, []);

  useEffect(() => {
    function onKeyboardEvent(event: Event) {
      const key = (event as CustomEvent<string>).detail;
      const time = videoRef.current?.currentTime ?? 0;
      if (key === "ArrowLeft") seek(time - 5);
      if (key === "ArrowRight") seek(time + 5);
      if (key === "Space") togglePlayback();
      if (key === "f") void videoRef.current?.requestFullscreen();
    }
    window.addEventListener("vidsearch:key", onKeyboardEvent);
    return () => window.removeEventListener("vidsearch:key", onKeyboardEvent);
  }, [seek, togglePlayback]);

  return (
    <section className="player-panel" aria-label={`Preview of ${video.filename}`}>
      <div className="player-frame">
        <video
          className="player-video"
          aria-label={`Video preview: ${video.filename}`}
          preload="metadata"
          ref={videoRef}
          src={resolveMediaUrl(video.media_url)}
          onDurationChange={(event) => {
            const value = event.currentTarget.duration;
            setDuration(Number.isFinite(value) ? value : null);
          }}
          onEnded={() => setPlaying(false)}
          onError={() => setPlaybackError("This file could not be decoded by the browser.")}
          onPause={() => setPlaying(false)}
          onPlay={() => setPlaying(true)}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        />
      </div>
      <div className="player-controls">
        <Timeline
          currentTime={currentTime}
          duration={duration}
          hits={timelineHits}
          onSeek={seek}
        />
        <div className="player-readout">
          <span className="current-time">{formatPlayerTime(currentTime)}</span>
          {startSeconds !== undefined && endSeconds !== undefined && (
            <span className="player-match-range">
              Match {formatPlayerTime(startSeconds)} – {formatPlayerTime(endSeconds)}
            </span>
          )}
        </div>
        <div className="player-meta">
          <div>
            <p className="player-title">{video.filename}</p>
            <p className="player-subtitle">{video.status === "ready" ? "Indexed video" : "Stored locally · not indexed"}</p>
          </div>
          <div className="player-actions">
            <Button aria-label="Back 5 seconds" onClick={() => seek(currentTime - 5)} size="icon" variant="ghost">
              <RotateCcw size={15} />
            </Button>
            <Button aria-label={playing ? "Pause video" : "Play video"} onClick={togglePlayback} size="icon" variant="ghost">
              {playing ? <Pause size={15} /> : <Play size={15} />}
            </Button>
            <Button aria-label="Forward 5 seconds" onClick={() => seek(currentTime + 5)} size="icon" variant="ghost">
              <RotateCw size={15} />
            </Button>
            <label className="speed-control">
              <span className="sr-only">Playback speed</span>
              <select
                aria-label="Playback speed"
                onChange={(event) => {
                  const value = Number(event.target.value);
                  setSpeed(value);
                  if (videoRef.current) videoRef.current.playbackRate = value;
                }}
                value={speed}
              >
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map((value) => (
                  <option key={value} value={value}>{value}×</option>
                ))}
              </select>
            </label>
            <Button aria-label="Fullscreen" onClick={() => void videoRef.current?.requestFullscreen()} size="icon" variant="ghost">
              <Maximize2 size={16} />
            </Button>
          </div>
        </div>
        {playbackError && <p className="player-error" role="alert">{playbackError}</p>}
      </div>
    </section>
  );
}

function formatPlayerTime(seconds: number): string {
  const safe = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const remainder = safe % 60;
  return hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}
