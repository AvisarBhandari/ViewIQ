"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SUGGESTIONS = [
  "Summarise this video",
  "What's the engagement rate?",
  "Compare the hooks in the first 5 seconds",
  "Which video performed better and why?",
];

// How fast to type characters when the full response arrives at once (ms per char).
// Real streaming (localhost) bypasses this entirely — tokens render immediately.
const TYPING_SPEED_MS = 8;

export default function ChatRoom({ session, videoIds = [] }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        videoIds.length === 1
          ? "Video loaded. Ask me anything about it — content, engagement, or improvement ideas."
          : "Videos loaded. Ask me anything — engagement, hooks, creator info, or comparisons.",
      sources: [],
      displayed: null, // null = fully shown (use content directly)
    },
  ]);
  const [question, setQuestion]               = useState("");
  const [streaming, setStreaming]             = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef    = useRef(null);
  const textareaRef  = useRef(null);
  const abortRef     = useRef(null);
  // Tracks running typing animations so they can be cancelled on Stop
  const typingTimers = useRef([]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Cancel all pending typing timers (used by Stop button)
  function cancelTyping() {
    typingTimers.current.forEach(clearTimeout);
    typingTimers.current = [];
  }

  // Animate `fullText` into the last assistant message character by character.
  // Called only when the entire response arrives in one chunk (Vercel buffered).
  const animateTyping = useCallback((fullText) => {
    cancelTyping();
    let i = 0;
    function step() {
      if (i > fullText.length) {
        // Animation done — collapse displayed back to null so content is used directly
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = { ...last, displayed: null };
          return updated;
        });
        return;
      }
      const slice = fullText.slice(0, i);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        updated[updated.length - 1] = { ...last, displayed: slice };
        return updated;
      });
      i++;
      const timer = setTimeout(step, TYPING_SPEED_MS);
      typingTimers.current.push(timer);
    }
    step();
  }, []);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function stopStreaming() {
    abortRef.current?.abort();
    abortRef.current = null;
    cancelTyping();
    setStreaming(false);
  }

  async function sendMessage() {
    const q = question.trim();
    if (!q || streaming) return;

    setShowSuggestions(false);
    setQuestion("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const history = messages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, { role: "user", content: q, sources: [], displayed: null }]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    setMessages((prev) => [...prev, { role: "assistant", content: null, sources: [], displayed: null }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, history, video_ids: videoIds }),
        signal: controller.signal,
      });

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let tokenCount = 0; // counts how many separate token chunks arrived

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            const data = JSON.parse(trimmed);

            if (data.type === "sources") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  sources: data.sources,
                };
                return updated;
              });
            }

            if (data.type === "token" && data.token) {
              tokenCount++;
              // Append to content immediately (real streaming path)
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = {
                  ...last,
                  content: (last.content ?? "") + data.token,
                };
                return updated;
              });
            }
          } catch {
            // incomplete JSON — skip
          }
        }
      }

      // Flush remaining buffer
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer.trim());
          if (data.type === "token" && data.token) {
            tokenCount++;
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = {
                ...last,
                content: (last.content ?? "") + data.token,
              };
              return updated;
            });
          }
        } catch {}
      }

      // If the whole response arrived in ≤3 token events it was buffered (Vercel).
      // Animate it so it feels like typing instead of a sudden drop.
      if (tokenCount <= 3) {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.content) animateTyping(last.content);
          return prev;
        });
      }

    } catch (err) {
      if (err.name === "AbortError") {
        cancelTyping();
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          // Freeze whatever was displayed at the time stop was pressed
          const frozen = last.displayed ?? last.content ?? "_Stopped._";
          updated[updated.length - 1] = { ...last, content: frozen, displayed: null };
          return updated;
        });
      } else {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Something went wrong. Please try again.",
            sources: [],
            displayed: null,
          };
          return updated;
        });
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }

  // What to actually render for a message:
  // - `displayed` is set during the typing animation (partial text)
  // - `content` is the full text (used directly for real streaming or after animation)
  function visibleContent(msg) {
    return msg.displayed !== null && msg.displayed !== undefined
      ? msg.displayed
      : msg.content;
  }

  const isLastActive = (i) =>
    (streaming || typingTimers.current.length > 0) &&
    i === messages.length - 1 &&
    messages[i].role === "assistant";

  const isWaiting =
    streaming && messages[messages.length - 1]?.content === null;

  const suggestions =
    videoIds.length === 1
      ? SUGGESTIONS.filter(
          (s) => !s.toLowerCase().includes("compare") && !s.toLowerCase().includes("which video")
        )
      : SUGGESTIONS;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-900">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">Chat</h2>
          <p className="text-xs text-zinc-400">
            {videoIds.length === 1
              ? "Analysing 1 video"
              : `Comparing ${videoIds.length} videos (${videoIds.map((id) => `Video ${id}`).join(", ")})`}
          </p>
        </div>
        {streaming && (
          <button
            onClick={stopStreaming}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-zinc-300 dark:border-zinc-600 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition"
          >
            <span className="w-2 h-2 rounded-sm bg-zinc-500 dark:bg-zinc-400 inline-block" />
            Stop
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {messages.map((msg, i) => (
          <div key={i}>
            <div className={`flex gap-2.5 items-end ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs border
                ${msg.role === "user"
                  ? "bg-blue-50 dark:bg-blue-950 border-transparent text-blue-500"
                  : "bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-500"}`}>
                {msg.role === "user" ? "U" : "✦"}
              </div>

              {visibleContent(msg) !== null && (
                <div className={`max-w-[78%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed
                  ${msg.role === "user"
                    ? "bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-100 rounded-br-sm"
                    : "bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700 rounded-bl-sm"}`}>
                  {msg.role === "assistant"
                    ? <MarkdownMessage content={visibleContent(msg)} />
                    : visibleContent(msg)}
                  {isLastActive(i) && (
                    <span className="inline-block w-0.5 h-3.5 bg-zinc-400 ml-0.5 animate-pulse align-middle" />
                  )}
                </div>
              )}
            </div>

            {msg.sources?.length > 0 && (
              <div className="flex gap-1.5 flex-wrap mt-2 ml-9">
                {msg.sources.map((s, j) => (
                  <span key={j} className="text-[11px] px-2 py-0.5 rounded-full border border-zinc-200 dark:border-zinc-700 text-zinc-500 bg-zinc-50 dark:bg-zinc-800">
                    Video {s.video_id} · chunk {s.chunk_index}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {isWaiting && (
          <div className="flex gap-2.5 items-end">
            <div className="w-7 h-7 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center text-xs text-zinc-500 flex-shrink-0">✦</div>
            <div className="bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1.5 items-center">
              {[0, 1, 2].map((j) => (
                <span key={j} className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: `${j * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {showSuggestions && (
        <div className="flex gap-2 px-4 pb-2 flex-wrap">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => { setQuestion(s); textareaRef.current?.focus(); }}
              className="text-xs px-3 py-1.5 rounded-full border border-zinc-200 dark:border-zinc-700 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors whitespace-nowrap"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-zinc-200 dark:border-zinc-800 px-4 py-3 flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={question}
          onChange={(e) => { setQuestion(e.target.value); autoResize(); }}
          onKeyDown={handleKey}
          placeholder="Ask about engagement, hooks, or request improvements…"
          rows={1}
          className="flex-1 resize-none rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-sm px-4 py-2.5 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-none focus:border-zinc-400 dark:focus:border-zinc-500 transition max-h-28 overflow-y-auto"
        />
        <button
          onClick={sendMessage}
          disabled={!question.trim() || streaming}
          className="w-9 h-9 rounded-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center flex-shrink-0 hover:opacity-80 active:scale-95 transition disabled:opacity-30"
          aria-label="Send"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function MarkdownMessage({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto my-2 rounded-lg border border-zinc-200 dark:border-zinc-700">
            <table className="text-xs w-full border-collapse" {...props} />
          </div>
        ),
        thead: ({ node, ...props }) => <thead className="bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200" {...props} />,
        th:    ({ node, ...props }) => <th className="px-3 py-2 text-left font-medium border-b border-zinc-300 dark:border-zinc-600 whitespace-nowrap" {...props} />,
        td:    ({ node, ...props }) => <td className="px-3 py-2 border-b border-zinc-100 dark:border-zinc-800 align-top leading-relaxed" {...props} />,
        tr:    ({ node, ...props }) => <tr className="even:bg-zinc-50 dark:even:bg-zinc-800/50" {...props} />,
        p:     ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
        strong:({ node, ...props }) => <strong className="font-medium" {...props} />,
        em:    ({ node, ...props }) => <em className="italic text-zinc-500 dark:text-zinc-400" {...props} />,
        code: ({ node, inline, ...props }) =>
          inline
            ? <code className="bg-zinc-200 dark:bg-zinc-700 px-1 py-0.5 rounded text-[11px] font-mono" {...props} />
            : <pre className="bg-zinc-200 dark:bg-zinc-700 p-3 rounded-lg text-[11px] font-mono overflow-x-auto my-2"><code {...props} /></pre>,
        ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-0.5 my-1" {...props} />,
        ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-0.5 my-1" {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}