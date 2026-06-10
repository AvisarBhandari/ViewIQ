export const runtime = "edge"; // ← THIS is the fix. Without this line Vercel
                                //   uses Node.js serverless which buffers the
                                //   entire response before sending it.
                                //   Edge runtime streams in real time.

const BACKEND_URL = process.env.BACKEND_URL;

export async function POST(request) {
  const body = await request.json();

  const backendRes = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!backendRes.ok || !backendRes.body) {
    return new Response("Backend error", { status: backendRes.status });
  }

  return new Response(backendRes.body, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "X-Accel-Buffering": "no",
      "Cache-Control": "no-cache, no-transform",
    },
  });
}