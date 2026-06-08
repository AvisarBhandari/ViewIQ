import { YoutubeTranscript } from "youtube-transcript";
export async function getTranscript(videoId) {
  const transcript =
    await YoutubeTranscript.fetchTranscript(videoId);

  return transcript
    .map((x) => x.text)
    .join(" ");
}

export async function getMetadata(videoId) {
  const response = await fetch(
    `https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=${videoId}&key=${process.env.NEXT_PUBLIC_YOUTUBE_API_KEY}`
  );

  const data = await response.json();

  const item = data.items[0];

  return {
    title: item.snippet.title,
    creator: item.snippet.channelTitle,
    views: Number(item.statistics.viewCount || 0),
    likes: Number(item.statistics.likeCount || 0),
    comments: Number(item.statistics.commentCount || 0),
    upload_date: item.snippet.publishedAt,
    duration: item.contentDetails.duration,
    hashtags: item.snippet.tags || [],
    thumbnail: item.snippet.thumbnails.high.url,
  };
}

export function getVideoId(url) {
  const match = url.match(
    /(?:v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/
  );

  if (!match) {
    throw new Error("Invalid YouTube URL");
  }

  return match[1];
}