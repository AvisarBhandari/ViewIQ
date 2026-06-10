import axios from "axios";

// All requests go through Next.js API routes — no NEXT_PUBLIC_API_URL needed in the browser.
// The API routes proxy to the real backend using the server-side BACKEND_URL env var.
const api = axios.create({
  baseURL: "/api",
});

export default api;