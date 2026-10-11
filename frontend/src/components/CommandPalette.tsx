import * as Dialog from "@radix-ui/react-dialog";
import { ArrowRight, Film, Search, Sun, Moon, Monitor, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ThemePreference } from "@/hooks/useTheme";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (path: string) => void;
  onUpload: () => void;
  preference: ThemePreference;
  onThemeChange: (preference: ThemePreference) => void;
  showShortcuts: boolean;
}

interface PaletteAction {
  label: string;
  hint?: string;
  icon: typeof Search;
  run: () => void;
}

function fuzzyMatch(value: string, query: string): boolean {
  let queryIndex = 0;
  for (const character of value.toLowerCase()) {
    if (character === query[queryIndex]) queryIndex += 1;
    if (queryIndex === query.length) return true;
  }
  return query.length === 0;
}

export function CommandPalette({
  open,
  onOpenChange,
  onNavigate,
  onUpload,
  preference,
  onThemeChange,
  showShortcuts,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const actions = useMemo<PaletteAction[]>(() => [
    { label: "Search videos", hint: "Go to search", icon: Search, run: () => onNavigate("/") },
    { label: "Open library", hint: "Browse local videos", icon: Film, run: () => onNavigate("/library") },
    { label: "Upload videos", hint: "Add local files", icon: Upload, run: onUpload },
    { label: "Use light theme", hint: "Color theme", icon: Sun, run: () => onThemeChange("light") },
    { label: "Use dark theme", hint: "Color theme", icon: Moon, run: () => onThemeChange("dark") },
    { label: "Use system theme", hint: "Color theme", icon: Monitor, run: () => onThemeChange("system") },
    { label: "Keyboard shortcuts", hint: " /  j/k  t  ?", icon: ArrowRight, run: () => setQuery("keyboard") },
  ], [onNavigate, onThemeChange, onUpload]);
  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return term ? actions.filter((action) =>
      fuzzyMatch(`${action.label} ${action.hint ?? ""}`, term),
    ) : actions;
  }, [actions, query]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActiveIndex(0);
      return;
    }
    setQuery(showShortcuts ? "keyboard" : "");
    setActiveIndex(0);
    inputRef.current?.focus();
  }, [open, showShortcuts]);

  function runActive(index = activeIndex) {
    const action = filtered[index];
    if (!action) return;
    action.run();
    if (action.label !== "Keyboard shortcuts") onOpenChange(false);
  }

  return (
    <Dialog.Root onOpenChange={onOpenChange} open={open}>
      <Dialog.Portal>
        <Dialog.Overlay className="palette-overlay" />
        <Dialog.Content
          aria-describedby="palette-description"
          className="command-palette"
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setActiveIndex((index) => Math.min(filtered.length - 1, index + 1));
            }
            if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveIndex((index) => Math.max(0, index - 1));
            }
            if (event.key === "Enter") {
              event.preventDefault();
              runActive();
            }
          }}
        >
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <p className="sr-only" id="palette-description">
            Search commands and move with the arrow keys.
          </p>
          <div className="palette-search">
            <Search aria-hidden="true" size={16} />
            <input
              aria-label="Filter commands"
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              placeholder="Type a command or search…"
              ref={inputRef}
              value={query}
            />
            <kbd>Esc</kbd>
          </div>
          <p className="palette-label">
            {query.toLowerCase() === "keyboard" ? "KEYBOARD SHORTCUTS" : "QUICK ACTIONS"}
          </p>
          {query.toLowerCase() === "keyboard" ? (
            <div className="shortcut-list">
              <span><kbd>/</kbd> Focus search</span>
              <span><kbd>j</kbd> <kbd>k</kbd> Move through results</span>
              <span><kbd>Space</kbd> Play or pause</span>
              <span><kbd>←</kbd> <kbd>→</kbd> Seek five seconds</span>
              <span><kbd>t</kbd> Cycle theme</span>
            </div>
          ) : (
            <div className="palette-options" role="listbox" aria-label="Commands">
              {filtered.map((action, index) => {
                const Icon = action.icon;
                const selected = index === activeIndex;
                return (
                  <button
                    aria-selected={selected}
                    className={`palette-item ${selected ? "palette-item-active" : ""}`}
                    key={action.label}
                    onClick={() => runActive(index)}
                    onMouseEnter={() => setActiveIndex(index)}
                    role="option"
                    type="button"
                  >
                    <Icon aria-hidden="true" size={15} />
                    <span>{action.label}</span>
                    <small>{action.label.includes("theme")
                      ? action.label === `Use ${preference} theme` ? "Current" : action.hint
                      : action.hint}</small>
                  </button>
                );
              })}
              {filtered.length === 0 && <p className="palette-no-results">No commands found</p>}
            </div>
          )}
          <div className="palette-footer">
            <span><kbd>↑</kbd> <kbd>↓</kbd> Navigate</span>
            <span><kbd>↵</kbd> Run</span>
            <span><kbd>Esc</kbd> Close</span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
