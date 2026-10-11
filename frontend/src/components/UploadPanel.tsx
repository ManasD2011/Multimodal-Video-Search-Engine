import * as Dialog from "@radix-ui/react-dialog";
import { Check, FolderUp, Upload, X } from "lucide-react";
import { useRef, useState, type DragEvent, type FormEvent, type ReactNode } from "react";
import { api, type VideoRecord } from "@/api/client";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/utils";

interface UploadPanelProps {
  onUploaded: (video: VideoRecord) => void;
  trigger?: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface UploadRow {
  name: string;
  size: number;
  status: "Uploading" | "Stored · not indexed" | "Upload failed";
}

export function UploadPanel({
  onUploaded,
  trigger,
  open: controlledOpen,
  onOpenChange,
}: UploadPanelProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rows, setRows] = useState<UploadRow[]>([]);
  const [url, setUrl] = useState("");
  const [urlMessage, setUrlMessage] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const open = controlledOpen ?? internalOpen;

  function updateOpen(value: boolean) {
    if (controlledOpen === undefined) setInternalOpen(value);
    onOpenChange?.(value);
    if (!value) {
      setUrlMessage(null);
      setUploadMessage(null);
    }
  }

  async function uploadFiles(files: FileList | File[]) {
    const selected = Array.from(files);
    if (selected.length === 0) return;
    setBusy(true);
    setUploadMessage(null);
    setRows(selected.map((file) => ({
      name: file.name,
      size: file.size,
      status: "Uploading",
    })));
    for (const [index, file] of selected.entries()) {
      try {
        const video = await api.uploadVideo(file);
        onUploaded(video);
        setRows((current) => current.map((row, rowIndex) =>
          rowIndex === index ? { ...row, status: "Stored · not indexed" } : row,
        ));
      } catch {
        setRows((current) => current.map((row, rowIndex) =>
          rowIndex === index ? { ...row, status: "Upload failed" } : row,
        ));
        setUploadMessage("One or more files could not be uploaded. Check the file type and size, then retry.");
      }
    }
    setBusy(false);
    if (inputRef.current) {
      inputRef.current.value = "";
      inputRef.current.removeAttribute("webkitdirectory");
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!busy) void uploadFiles(event.dataTransfer.files);
  }

  function validateUrl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUrlMessage("URL imports are not connected to this API yet. Upload a video file instead.");
    setUrl("");
  }

  return (
    <Dialog.Root onOpenChange={updateOpen} open={open}>
      {trigger && <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>}
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="upload-dialog">
          <div className="dialog-heading">
            <div>
              <p className="eyebrow">LOCAL LIBRARY</p>
              <Dialog.Title className="dialog-title">Add videos</Dialog.Title>
              <Dialog.Description className="dialog-description">
                Video files are stored locally and can be previewed in the library.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <Button aria-label="Close upload dialog" size="icon" variant="ghost">
                <X size={16} />
              </Button>
            </Dialog.Close>
          </div>

          <input
            accept=".mp4,.mkv,.mov,.webm,.avi,video/*"
            className="sr-only"
            disabled={busy}
            multiple
            onChange={(event) => void uploadFiles(event.target.files ?? [])}
            ref={inputRef}
            type="file"
          />
          <div
            className="upload-dropzone"
            onDragOver={(event) => event.preventDefault()}
            onDrop={onDrop}
          >
            <Upload aria-hidden="true" className="upload-icon" size={18} />
            <strong>Drop videos or a folder</strong>
            <span>MP4, MOV, MKV, WebM or AVI · 2 GB max per file</span>
            <div className="upload-actions">
              <Button
                disabled={busy}
                onClick={() => {
                  inputRef.current?.removeAttribute("webkitdirectory");
                  inputRef.current?.click();
                }}
                size="sm"
                variant="secondary"
              >
                Choose videos
              </Button>
              <Button
                disabled={busy}
                onClick={() => {
                  inputRef.current?.setAttribute("webkitdirectory", "");
                  inputRef.current?.click();
                }}
                size="sm"
                variant="ghost"
              >
                <FolderUp size={14} /> Choose folder
              </Button>
            </div>
          </div>
          <p className="upload-limit">
            Only local files are uploaded. Indexing is not connected yet.
          </p>

          {rows.length > 0 && (
            <ul className="upload-rows" aria-live="polite">
              {rows.map((row, index) => (
                <li className="upload-row" key={`${row.name}-${index}`}>
                  <div className="upload-row-main">
                    <span className="upload-file-name">{row.name}</span>
                    <span className="upload-row-meta">{formatBytes(row.size)} · {row.status}</span>
                  </div>
                  {row.status === "Stored · not indexed" && (
                    <Check aria-label="Stored" className="upload-check" size={15} />
                  )}
                  {row.status === "Uploading" && <span aria-label="Uploading" className="upload-progress" />}
                </li>
              ))}
            </ul>
          )}
          {uploadMessage && <p className="form-error" role="alert">{uploadMessage}</p>}

          <form className="url-import" onSubmit={validateUrl}>
            <label htmlFor="video-url">Import from URL</label>
            <div>
              <input
                id="video-url"
                onChange={(event) => setUrl(event.target.value)}
                placeholder="Paste a YouTube URL"
                value={url}
              />
              <Button disabled={!url.trim()} size="sm" type="submit" variant="secondary">
                Check URL
              </Button>
            </div>
            {urlMessage && <p role="status">{urlMessage}</p>}
          </form>

          <div className="dialog-footer">
            <span><Check size={13} /> Files stay in your local data directory</span>
            <Dialog.Close asChild><Button size="sm" variant="ghost">Done</Button></Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
