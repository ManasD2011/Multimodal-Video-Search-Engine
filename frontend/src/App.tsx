import { Command, Film, Search as SearchIcon, Upload } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { ApiError, api, type HealthResponse, type VideoRecord } from "@/api/client";
import { CommandPalette } from "@/components/CommandPalette";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UploadPanel } from "@/components/UploadPanel";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/useTheme";
import { LibraryPage } from "@/pages/Library";
import { SearchPage } from "@/pages/Search";

function isEditableTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLElement &&
    (target.isContentEditable || Boolean(target.closest("input, textarea, select, [contenteditable='true']")));
}

export default function App() {
  const navigate = useNavigate();
  const { preference, setPreference, cycle } = useTheme();
  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [loadingLibrary, setLoadingLibrary] = useState(true);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [themeAnnouncement, setThemeAnnouncement] = useState("");

  const refreshVideos = useCallback(async (showLoading = true) => {
    if (showLoading) setLoadingLibrary(true);
    setLibraryError(null);
    try {
      setVideos(await api.listVideos());
    } catch (cause) {
      setLibraryError(
        cause instanceof ApiError && cause.status === 0
          ? "Start the local API to load your library."
          : "The video library could not be loaded. Retry after checking the API.",
      );
    } finally {
      if (showLoading) setLoadingLibrary(false);
    }
  }, []);

  useEffect(() => {
    void refreshVideos();
    void api.health().then(setHealth).catch(() => setHealth(null));
  }, [refreshVideos]);

  useEffect(() => {
    if (!videos.some((video) => video.status === "indexing")) return;
    const interval = window.setInterval(() => {
      void refreshVideos(false);
    }, 2000);
    return () => window.clearInterval(interval);
  }, [refreshVideos, videos]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
        return;
      }
      if (isEditableTarget(event.target)) return;
      if (event.key.toLowerCase() === "t") {
        event.preventDefault();
        cycle();
        const next = preference === "system" ? "light" : preference === "light" ? "dark" : "system";
        setThemeAnnouncement(`${next[0].toUpperCase()}${next.slice(1)} theme`);
        return;
      }
      if (event.key === "?" || (event.shiftKey && event.code === "Slash")) {
        event.preventDefault();
        setShortcutsOpen(true);
        setPaletteOpen(true);
        return;
      }
      if (event.key === "/") {
        event.preventDefault();
        document.getElementById("video-search")?.focus();
        return;
      }
      const supportedKeys = ["j", "k", "[", "]", "ArrowLeft", "ArrowRight", " ", "f", "Enter"];
      if (!supportedKeys.includes(event.key)) return;
      const target = event.target instanceof HTMLElement ? event.target : null;
      if ((event.key === " " || event.key === "Enter") &&
          target?.closest("button, a, [role='button'], [role='option']")) return;
      event.preventDefault();
      window.dispatchEvent(new CustomEvent("vidsearch:key", {
        detail: event.key === " " ? "Space" : event.key,
      }));
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [cycle, preference]);

  function addVideo(video: VideoRecord) {
    setVideos((current) => [
      video,
      ...current.filter((item) => item.video_id !== video.video_id),
    ]);
  }

  const navigateFromPalette = (path: string) => {
    navigate(path);
    setPaletteOpen(false);
  };

  return (
    <div className="app-frame">
      <header className="topbar">
        <Link aria-label="Vidsearch home" className="brand" to="/">
          vidsearch<span>.</span>
        </Link>
        <nav aria-label="Main navigation" className="main-nav">
          <NavLink className={({ isActive }) => `nav-link ${isActive ? "nav-active" : ""}`} end to="/">
            <SearchIcon aria-hidden="true" size={14} /> Search
          </NavLink>
          <NavLink className={({ isActive }) => `nav-link ${isActive ? "nav-active" : ""}`} to="/library">
            <Film aria-hidden="true" size={14} /> Library <span className="nav-count">{videos.length}</span>
          </NavLink>
        </nav>
        <div className="topbar-right">
          <Button
            aria-label="Open command palette"
            className="command-trigger"
            onClick={() => {
              setShortcutsOpen(false);
              setPaletteOpen(true);
            }}
            size="sm"
            variant="ghost"
          >
            <Command aria-hidden="true" size={13} /> <kbd>⌘K</kbd>
          </Button>
          <ThemeToggle
            onChange={(next) => {
              setPreference(next);
              setThemeAnnouncement(`${next[0].toUpperCase()}${next.slice(1)} theme`);
            }}
            value={preference}
          />
          <span className={`connection-state ${health ? "connected" : ""}`} title={health ? "API connected" : "API unavailable"}>
            <span className="status-dot" /> {health ? "LOCAL" : "OFFLINE"}
          </span>
          <Button
            aria-label="Upload videos"
            className="header-upload"
            onClick={() => setUploadOpen(true)}
            size="sm"
            variant="secondary"
          >
            <Upload aria-hidden="true" size={14} /> Add videos
          </Button>
        </div>
      </header>

      <Routes>
        <Route
          element={<SearchPage onOpenUpload={() => setUploadOpen(true)} videoCount={videos.length} videos={videos} />}
          path="/"
        />
        <Route
          element={
            <LibraryPage
              error={libraryError}
              loading={loadingLibrary}
              onOpenUpload={() => setUploadOpen(true)}
              onRefresh={refreshVideos}
              videos={videos}
            />
          }
          path="/library"
        />
        <Route
          element={<SearchPage onOpenUpload={() => setUploadOpen(true)} videoCount={videos.length} videos={videos} />}
          path="*"
        />
      </Routes>

      <footer className="site-footer">
        <span>VIDSEARCH <span>/</span> MULTIMODAL VIDEO SEARCH</span>
        <span>INDEX <b>{health?.search_ready ? "READY" : "NOT CONNECTED"}</b></span>
      </footer>
      <span aria-live="polite" className="sr-only">{themeAnnouncement}</span>

      <UploadPanel
        onOpenChange={setUploadOpen}
        onUploaded={addVideo}
        open={uploadOpen}
        videos={videos}
      />
      <CommandPalette
        onNavigate={navigateFromPalette}
        onOpenChange={(open) => {
          setPaletteOpen(open);
          if (!open) setShortcutsOpen(false);
        }}
        onThemeChange={(next) => {
          setPreference(next);
          setThemeAnnouncement(`${next[0].toUpperCase()}${next.slice(1)} theme`);
        }}
        onUpload={() => setUploadOpen(true)}
        open={paletteOpen}
        preference={preference}
        showShortcuts={shortcutsOpen}
      />
    </div>
  );
}
