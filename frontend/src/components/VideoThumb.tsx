import { resolveMediaUrl, type VideoRecord } from "@/api/client";

interface VideoThumbProps {
  video: VideoRecord;
  atSeconds?: number;
}

export function VideoThumb({ video, atSeconds = 0 }: VideoThumbProps) {
  return (
    <video
      aria-label={`Frame from ${video.filename}`}
      className="video-thumb"
      muted
      preload="metadata"
      src={`${resolveMediaUrl(video.media_url)}#t=${Math.max(0, atSeconds)}`}
    />
  );
}
