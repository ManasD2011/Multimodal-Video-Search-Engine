import { ArrowRight, Search, SlidersHorizontal } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SearchBarProps {
  busy: boolean;
  count: number | null;
  latencyMs: number | null;
  onSearch: (query: string) => void;
}

export function SearchBar({ busy, count, latencyMs, onSearch }: SearchBarProps) {
  const [query, setQuery] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (query.trim() && !busy) onSearch(query.trim());
  }

  return (
    <div className="search-composer">
      <form className="search-form" onSubmit={submit}>
        <Search aria-hidden="true" className="search-glyph" size={16} />
        <Input
          aria-label="Search video library"
          autoComplete="off"
          className="search-input"
          id="video-search"
          maxLength={2000}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="man in red shirt carrying a bag"
          value={query}
        />
        <div className="search-meta" aria-live="polite">
          {busy
            ? "Searching…"
            : count === null
              ? "⌘K"
              : `${count} matches${latencyMs === null ? "" : ` · ${(latencyMs / 1000).toFixed(2)}s`}`}
        </div>
        <Button aria-label="Run search" disabled={busy || !query.trim()} size="sm" type="submit">
          Search <ArrowRight size={14} />
        </Button>
      </form>
      <div className="search-scope">
        <SlidersHorizontal size={13} aria-hidden="true" />
        <button className="scope-chip active" type="button">All videos</button>
        <span className="scope-note">Search what appears on screen and what is spoken</span>
      </div>
    </div>
  );
}
