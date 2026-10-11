import { formatTime } from "@/lib/utils";

export interface TimelineHit {
  start: number;
  end: number;
  score: number;
}

interface TimelineProps {
  duration: number | null;
  currentTime: number;
  onSeek: (seconds: number) => void;
  hits?: TimelineHit[];
}

export function Timeline({
  duration,
  currentTime,
  onSeek,
  hits = [],
}: TimelineProps) {
  const progress = duration && duration > 0
    ? Math.min(100, (currentTime / duration) * 100)
    : 0;
  const ticks = Array.from({ length: 21 }, (_, index) => index * 5);
  return (
    <div className="timeline-wrap">
      <div
        aria-label="Video timeline"
        className="timeline-track"
        onClick={(event) => {
          if (!duration) return;
          const bounds = event.currentTarget.getBoundingClientRect();
          if (bounds.width > 0)
            onSeek(((event.clientX - bounds.left) / bounds.width) * duration);
        }}
        role="slider"
        tabIndex={duration ? 0 : -1}
        aria-valuemin={0}
        aria-valuemax={duration ?? 0}
        aria-valuenow={currentTime}
        aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
      >
        {ticks.map((tick) => (
          <span aria-hidden="true" className="timeline-tick" key={tick} style={{ left: `${tick}%` }} />
        ))}
        {duration &&
          hits.map((hit, index) => (
            <span
              aria-hidden="true"
              className="timeline-hit"
              key={`${hit.start}-${index}`}
              style={{
                left: `${(hit.start / duration) * 100}%`,
                width: `${Math.max(0.5, ((hit.end - hit.start) / duration) * 100)}%`,
                opacity: Math.max(0.5, Math.min(1, hit.score)),
              }}
            />
          ))}
        <span className="timeline-progress" style={{ width: `${progress}%` }} />
        <span className="timeline-playhead" style={{ left: `${progress}%` }} />
      </div>
      <div className="timeline-times">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
      {hits.length > 0 && (
        <ol className="sr-only">
          {hits.map((hit, index) => (
            <li key={`${hit.start}-${index}`}>
              Match {index + 1} of {hits.length}, {formatTime(hit.start)} to {formatTime(hit.end)}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
