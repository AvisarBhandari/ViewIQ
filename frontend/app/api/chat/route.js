const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request) {
  const body = await request.json();

  const backendRes = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!backendRes.ok) {
    return new Response("Backend error", { status: backendRes.status });
  }

  // Pass the backend stream straight through with headers that tell
  // Vercel/the browser NOT to buffer — this is what makes it feel live.
  return new Response(backendRes.body, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
      "X-Accel-Buffering": "no",   // disables Nginx/Vercel proxy buffering
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}