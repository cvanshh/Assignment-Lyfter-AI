# Relay: LLM chatbot with key failover and response caching

FastAPI + LiteLLM + SQLite backend, React (Vite) frontend, Docker for everything.

## 1. Live URLs
- Frontend: `https://<your-frontend>.onrender.com`
- Backend: `https://<your-backend>.onrender.com` (try `/health`)
- Demo video: `<link>`

## 2. Run locally
**With Docker**
```bash
cp .env.example .env     # add 2+ real Gemini keys to LLM_API_KEYS
make up                  # frontend :3000, backend :8000
make down
```
**Without Docker (Windows PowerShell)**
```powershell
cp .env.example .env     # add 2+ real Gemini keys to LLM_API_KEYS (or set LLM_MOCK=true for offline demo)
# One-command launcher (starts backend :8000 and frontend :3000):
.\start.ps1
```
Or run manually:
```powershell
# backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# frontend (requires Node.js, or serve frontend/dist)
cd frontend
npm install; npm run dev
```
Tests (no real keys needed, uses LiteLLM's mock mode):
```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest -v
```

**Deploying to Render (Free Tier Ready)**:
1. Push this repo (`lyftr-chatbot`) to GitHub.
2. In Render Dashboard: **New > Blueprint** and select your repo (`render.yaml` is pre-configured on the `free` plan and auto-wires `VITE_API_URL` from `relay-backend` to `relay-frontend`).
3. In `relay-backend` Environment settings, set:
   - `LLM_API_KEYS`: your comma-separated Gemini API keys (`key1,key2`) — or set `LLM_MOCK=true` for an offline demo.
   - `ALLOWED_ORIGINS`: your deployed `relay-frontend` URL (e.g. `https://relay-frontend.onrender.com`, no trailing slash).
4. Alternatives: backend on Fly.io/Railway/HF Spaces, frontend on Vercel/Netlify (build `npm run build`, output `dist`, env `VITE_API_URL`). For persistent SQLite on Render, upgrade `relay-backend` to `plan: starter` and uncomment `disk:` in `render.yaml`.

## 3. Design decisions
- **Key fallback.** `llm.complete()` walks the pool in order and calls `litellm.acompletion` with one key at a time. Any failure (429, quota, 5xx, auth, timeout, empty reply) moves to the next key. If all fail, a clean `503 {"detail":"all providers unavailable"}` is returned and nothing is stored. A real failure puts that key on a 30 s cooldown (it is tried last, never dropped), so a dead key doesn't add latency to every request. Simulated failures never trigger cooldown. I used an explicit loop instead of `Router` so key ids, attempts and the simulation hook are exact.
- **Caching.** LiteLLM's built-in cache (`local` in-memory, or `disk` via `CACHE_TYPE`). The key is model + the full message list, independent of which API key is used, so the same first message in a new session is a hit and any different message is a miss. A hit is detected from LiteLLM's `cache_hit` flag; it reports `key_id: null`, `fallback_attempts: 0` and the stored token usage. Requests carrying `X-Simulate-Failure` bypass the cache so they always return a real, fresh answer.
- **SQLite sessions.** Path comes from `DATABASE_URL` (a Docker volume at `/data`). Schema is created on startup, WAL mode on. A turn (user + assistant rows) is written in one transaction only after success, so failed requests never pollute history. A small `sessions` table stores the per-session system prompt. The client sends only the new message; the server rebuilds the context.
- **Security.** Keys live only in env vars, are never logged or returned (only `key_1`...), CORS is restricted to `ALLOWED_ORIGINS`, input is validated, all errors are JSON, the container runs as non-root, and the failure hook is off unless `ENABLE_FAILURE_SIMULATION=true`.

## 4. Verification
```bash
B=https://<backend>
curl $B/health
# live, then cache hit from a brand-new session (same reply, key_id null, faster)
curl -s $B/chat -H 'content-type: application/json' -d '{"session_id":"a1","message":"What is the capital of France?"}'
curl -s $B/chat -H 'content-type: application/json' -d '{"session_id":"b2","message":"What is the capital of France?"}'
# failover: key_1 fails, key_2 answers
curl -s $B/chat -H 'content-type: application/json' -H 'X-Simulate-Failure: key_1=429' -d '{"session_id":"c3","message":"hello"}'
# all keys fail: 503, nothing stored
curl -si $B/chat -H 'content-type: application/json' -H 'X-Simulate-Failure: *=429' -d '{"session_id":"d4","message":"hello"}'
curl -s $B/sessions/a1/messages
```
In the UI: every reply shows source, model, latency and per-request tokens. Use **Replay first message in new chat** for an instant cache hit, and the **Failure simulator** to watch the key pool react.

## 5. Setup Used
Claude (Anthropic) for scaffolding and review; VS Code; pytest; Docker Desktop. <edit with your own tools>

## 6. Bonus features
- **Routing trail on every reply** (`key_1 failed (429)` then `key_2 answered`, or `Served from cache`): failover is visible, not hidden. Backed by an extra `attempts` field in `metadata`.
- **Live key-pool panel** showing which key answered, failed or stood by.
- **One-click failure simulator** driving `X-Simulate-Failure`, for demos without exhausting real keys.
- **Replay in new chat** to demonstrate cross-session cache hits in one click.
- **Key cooldown** so dead keys don't slow every request.
- Per-session system prompt (persisted), readable error messages for 422/503/network failures.
