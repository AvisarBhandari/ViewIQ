const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function DELETE(request, { params }) {
  const { video_id } = await params;
  const res = await fetch(`${BACKEND_URL}/remove/${video_id}`, { method: "DELETE" });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}