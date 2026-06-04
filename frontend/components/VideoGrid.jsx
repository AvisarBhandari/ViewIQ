"use client";
import { useState } from "react";
import api from "@/lib/api";

const LABELS = ["A", "B", "C", "D", "E"];

function getYouTubeId(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtu.be")) return u.pathname.slice(1);
    return u.searchParams.get("v");
  } catch {
    return null;
  }
}

function engagementRate(meta) {
  if (meta?.engagement_rate != null && !isNaN(Number(meta.engagement_rate))) {
    return Number(meta.engagement_rate).toFixed(2) + "%";
  }
  const views = Number(meta?.views) || 0;
  const likes = Number(meta?.likes) || 0;
  const comments = Number(meta?.comments) || 0;
  if (!views) return "—";
  return ((likes + comments) / views * 100).toFixed(2) + "%";
}

function fmtNum(n) {
  const num = Number(n);
  if (!num || isNaN(num)) return "—";
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
  if (num >= 1_000) return (num / 1_000).toFixed(1) + "K";
  return String(num);
}

function VideoCard({ label, data, onRemove }) {
  const [expanded, setExpanded] = useState(false);

  if (!data?.metadata) {
    return (
      <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">{label}</span>
          <button onClick={onRemove} className="text-xs text-zinc-400 hover:text-red-500 transition">✕</button>
        </div>
        <p className="text-xs text-red-400 text-center py-4">
          Failed to load.{" "}
          <button onClick={onRemove} className="underline">Remove</button>
        </p>
      </div>
    );
  }

  const meta = data.metadata;
  const sourceUrl = meta.source_url || meta.source || "";
  const ytId = getYouTubeId(sourceUrl);

  return (
    <div className="border-b border-zinc-200 dark:border-zinc-800">
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">{label}</span>
          <button
            onClick={onRemove}
            className="text-xs text-zinc-400 hover:text-red-500 transition"
            aria-label="Remove video"
          >
            ✕
          </button>
        </div>

        <div className="w-full aspect-video bg-zinc-100 dark:bg-zinc-800 rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-700 mb-3 relative">
          {ytId ? (
            expanded ? (
              <iframe
                src={`https://www.youtube.com/embed/${ytId}?autoplay=1`}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <button
                onClick={() => setExpanded(true)}
                className="w-full h-full flex items-center justify-center group relative"
              >
                <img
                  src={`https://img.youtube.com/vi/${ytId}/hqdefault.jpg`}
                  alt={meta.title || "thumbnail"}
                  className="w-full h-full object-cover absolute inset-0"
                />
                <div className="relative z-10 w-12 h-12 rounded-full bg-black/70 flex items-center justify-center group-hover:bg-black/90 transition">
                  <svg className="w-5 h-5 text-white ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7L8 5z" />
                  </svg>
                </div>
              </button>
            )
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <svg className="w-8 h-8 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7L8 5z" />
              </svg>
            </div>
          )}
        </div>

        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 line-clamp-2 mb-1">
          {meta.title || "Untitled"}
        </p>
        <p className="text-xs text-zinc-500 mb-3">
          {[meta.creator, meta.duration ? `${Math.floor(meta.duration / 60)}m` : null]
            .filter(Boolean).join(" · ") || "—"}
        </p>

        <div className="grid grid-cols-3 gap-1.5">
          {[
            { label: "Views",     value: fmtNum(meta.views) },
            { label: "Likes",     value: fmtNum(meta.likes) },
            { label: "Eng. rate", value: engagementRate(meta), highlight: true },
          ].map((s) => (
            <div key={s.label} className="bg-zinc-50 dark:bg-zinc-800 rounded-md p-2">
              <div className="text-[10px] text-zinc-400">{s.label}</div>
              <div className={`text-sm font-medium ${
                s.highlight ? "text-green-600 dark:text-green-400" : "text-zinc-900 dark:text-zinc-100"
              }`}>
                {s.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function VideoGrid({ videos, onAddVideo, onRemoveVideo }) {
  // Defensive: always treat as array even if parent passes something wrong
  const safeVideos = Array.isArray(videos) ? videos : [];

  const [urlInput, setUrlInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAdd(e) {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const nextLabel = LABELS[safeVideos.length] ?? String(safeVideos.length + 1);
      const res = await api.post("/ingest-one", {
        url: urlInput,
        video_id: nextLabel,
      });
      onAddVideo(res.data.data);
      setUrlInput("");
    } catch (err) {
      setError(err.response?.data?.message || "Failed to add video.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
        <h2 className="text-sm font-medium text-zinc-900 dark:text-zinc-100 mb-3">Videos</h2>
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Add YouTube URL…"
            className="flex-1 min-w-0 text-xs border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 rounded-lg px-3 py-2 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 transition"
          />
          <button
            type="submit"
            disabled={loading || !urlInput.trim() || safeVideos.length >= 5}
            className="text-xs px-3 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 disabled:opacity-40 transition hover:opacity-90 whitespace-nowrap"
          >
            {loading ? "…" : "Add"}
          </button>
        </form>
        {error && <p className="text-xs text-red-500 mt-1.5">{error}</p>}
      </div>

      <div className="overflow-y-auto flex-1">
        {safeVideos.map((v, i) => (
          <VideoCard
            key={i}
            label={LABELS[i] ?? String(i + 1)}
            data={v}
            onRemove={() => onRemoveVideo(i)}
          />
        ))}
        {safeVideos.length === 0 && (
          <p className="text-xs text-zinc-400 text-center py-8">No videos loaded.</p>
        )}
      </div>
    </div>
  );
}