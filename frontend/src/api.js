const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function getHealth() {
  const res = await fetch(`${BASE}/health`);
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON */ }
  if (!res.ok) {
    const err = new Error(body?.detail || `Backend returned ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return body;
}

function explain(status, detail) {
  if (status === 503) return "Every API key in the pool is unavailable right now. Wait a moment, then send again.";
  if (status === 422) {
    const first = Array.isArray(detail) ? detail[0]?.msg : detail;
    return `Message not sent: ${first || "invalid input"}. Messages must be 1 to 4000 characters.`;
  }
  return typeof detail === "string" ? detail : "The server hit an unexpected error. Try again.";
}

export async function sendChat({ session_id, message, system_prompt, simulate }) {
  const headers = { "Content-Type": "application/json" };
  if (simulate) headers["X-Simulate-Failure"] = simulate;
  let res;
  try {
    res = await fetch(`${BASE}/chat`, { method: "POST", headers, body: JSON.stringify({ session_id, message, system_prompt }) });
  } catch {
    throw new Error("Can't reach the backend. Check your connection or the backend URL.");
  }
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) throw new Error(explain(res.status, body?.detail));
  return body;
}
