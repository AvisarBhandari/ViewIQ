"use client";
import { useState } from "react";
import api from "@/lib/api";

export default function UrlForm({ onSuccess }) {
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [twoVideos, setTwoVideos] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!urlA.trim()) {
      setError("Please enter at least one video URL.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/ingest", {
        url_a: urlA,
        url_b: twoVideos && urlB.trim() ? urlB : null,
      });

      if (res.data.status === "error") {
        setError(res.data.message);
        return;
      }

      onSuccess(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to analyze video(s).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center p-6 bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-lg">
        <div className="mb-8">
          <h1 className="text-2xl font-medium text-zinc-900 dark:text-zinc-100 mb-1">
            Video analysis
          </h1>
          <p className="text-sm text-zinc-500">
            Analyse one video in depth, or paste two to compare them side by side.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Video A — always shown */}
          <div>
            <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wide">
              {twoVideos ? "Video A — YouTube" : "Video URL — YouTube"}
            </label>
            <input
              value={urlA}
              onChange={(e) => setUrlA(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 rounded-lg px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 dark:focus:border-zinc-500 transition"
            />
          </div>

          {/* Toggle — add second video */}
          <button
            type="button"
            onClick={() => { setTwoVideos((v) => !v); setUrlB(""); }}
            className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition"
          >
            <span className={`w-4 h-4 rounded border flex items-center justify-center transition
              ${twoVideos
                ? "bg-zinc-900 dark:bg-zinc-100 border-zinc-900 dark:border-zinc-100"
                : "border-zinc-300 dark:border-zinc-600"}`}
            >
              {twoVideos && (
                <svg className="w-2.5 h-2.5 text-white dark:text-zinc-900" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M2 6l3 3 5-5" />
                </svg>
              )}
            </span>
            Compare with a second video
          </button>

          {/* Video B — shown only when toggled */}
          {twoVideos && (
            <div>
              <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wide">
                Video B — YouTube
              </label>
              <input
                value={urlB}
                onChange={(e) => setUrlB(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 rounded-lg px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 dark:focus:border-zinc-500 transition"
              />
            </div>
          )}

          {error && <p className="text-xs text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-sm font-medium py-2.5 rounded-lg disabled:opacity-40 transition hover:opacity-90"
          >
            {loading
              ? twoVideos ? "Analysing both videos…" : "Analysing video…"
              : twoVideos ? "Analyse & compare" : "Analyse video"}
          </button>
        </form>
      </div>
    </div>
  );
}