"use client";
import { useState } from "react";
import UrlForm from "@/components/UrlForm";
import VideoGrid from "@/components/VideoGrid";
import ChatRoom from "@/components/ChatRoom";

export default function Home() {
  const [videos, setVideos] = useState(null);

  function handleIngestSuccess(data) {
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

  // Gate: never render VideoGrid or ChatRoom until videos is a populated array
  if (!Array.isArray(videos) || videos.length === 0) {
    return <UrlForm onSuccess={handleIngestSuccess} />;
  }

  return (
    <div className="h-screen flex overflow-hidden bg-zinc-50 dark:bg-zinc-950">
      <div className="w-80 flex-shrink-0 border-r border-zinc-200 dark:border-zinc-800 overflow-hidden flex flex-col">
        <VideoGrid
          videos={videos}
          onAddVideo={addVideo}
          onRemoveVideo={removeVideo}
        />
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatRoom session={{ videos }} />
      </div>
    </div>
  );
}