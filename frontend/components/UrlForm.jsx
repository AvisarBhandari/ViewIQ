"use client";
import { useState } from "react";
import api from "@/lib/api";

export default function UrlForm({ onSuccess }) {
  const [urlA, setUrlA] = useState("");
  const [urlB, setUrlB] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!urlA.trim() || !urlB.trim()) {
      setError("Please enter both video URLs.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/ingest", { url_a: urlA, url_b: urlB });
      onSuccess(res.data.data); // expects { videoA: {...}, videoB: {...} }
    } catch (err) {
      setError(err.response?.data?.message || "Failed to analyze videos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center p-6 bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-lg">
        <div className="mb-8">
          <h1 className="text-2xl font-medium text-zinc-900 dark:text-zinc-100 mb-1">
            Video comparison
          </h1>
          <p className="text-sm text-zinc-500">
            Paste two video URLs to compare engagement and get AI insights.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wide">
              Video A — YouTube
            </label>
            <input
              value={urlA}
              onChange={(e) => setUrlA(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 rounded-lg px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 dark:focus:border-zinc-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wide">
              Video B — Instagram Reel
            </label>
            <input
              value={urlB}
              onChange={(e) => setUrlB(e.target.value)}
              placeholder="https://instagram.com/reel/..."
              className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 rounded-lg px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 dark:focus:border-zinc-500 transition"
            />
          </div>

          {error && (
            <p className="text-xs text-red-500">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-sm font-medium py-2.5 rounded-lg disabled:opacity-40 transition hover:opacity-90"
          >
            {loading ? "Analyzing both videos…" : "Analyze & compare"}
          </button>
        </form>
      </div>
    </div>
  );
}