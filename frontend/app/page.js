"use client";
import { useState } from "react";
import api from "@/lib/api";
import UrlForm from "@/components/UrlForm";
import VideoGrid from "@/components/VideoGrid";
import ChatRoom from "@/components/ChatRoom";

const LABELS = ["A", "B", "C", "D"];

export default function Home() {
  const [videos, setVideos] = useState(null);

  function handleIngestSuccess(data) {
    // data = { videoA?: {...}, videoB?: {...} }
    const initial = [data.videoA, data.videoB].filter(Boolean);
    setVideos(initial.length > 0 ? initial : null);
  }

  function addVideo(video) {
    setVideos((prev) => [...(prev ?? []), video]);
  }

  function removeVideo(index) {
    setVideos((prev) => {
      const next = (prev ?? []).filter((_, i) => i !== index);
      return next.length === 0 ? null : next;
    });
  }

  async function handleReset() {
    // Wipe backend vector store then return to landing page
    try { await api.post("/clear"); } catch { /* best-effort */ }
    setVideos(null);
  }

  if (!Array.isArray(videos) || videos.length === 0) {
    return <UrlForm onSuccess={handleIngestSuccess} />;
  }

  // Derive the video_ids in the same order as the videos array
  // Each video carries its video_id from the backend response
  const videoIds = videos.map((v, i) => v?.video_id || LABELS[i]);

  return (
    <div className="h-screen flex overflow-hidden bg-zinc-50 dark:bg-zinc-950">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 border-r border-zinc-200 dark:border-zinc-800 overflow-hidden flex flex-col">
        <VideoGrid
          videos={videos}
          onAddVideo={addVideo}
          onRemoveVideo={removeVideo}
        />
        {/* Reset session */}
        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
          <button
            onClick={handleReset}
            className="w-full text-xs py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 text-zinc-500 hover:text-red-500 hover:border-red-300 dark:hover:border-red-700 transition"
          >
            Clear session &amp; start over
          </button>
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <ChatRoom session={{ videos }} videoIds={videoIds} />
      </div>
    </div>
  );
}