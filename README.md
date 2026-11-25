Relay | Resilient LLM Chatbot

Building reliable AI conversations with automatic API failover, intelligent caching, and persistent session management.

Relay is a full-stack LLM chatbot built with React, FastAPI, LiteLLM, and SQLite. It improves application reliability by handling API failures automatically, reducing redundant model calls, and maintaining contextual conversations.

<p align="center">  <a href="https://assignment-lyfter-ai.vercel.app/">
    <img src="https://img.shields.io/badge/Live%20Demo-Visit%20App-blue?style=for-the-badge" />
  </a>
  <a href="https://drive.google.com/file/d/1nnplIg33chDTSIYpJa7ZNr1NzXY-K1CM/view?usp=drivesdk">
    <img src="https://img.shields.io/badge/Watch-Demo%20Video-red?style=for-the-badge" />
  </a></p>---

Live Deployment

- Frontend: "Relay Web Application" (https://assignment-lyfter-ai.vercel.app/)
- Backend: "Render Backend" (https://assignment-lyfter-ai-1.onrender.com)
- Demo Video: "Watch Project Demonstration" (https://drive.google.com/file/d/1nnplIg33chDTSIYpJa7ZNr1NzXY-K1CM/view?usp=drivesdk)

---

Tech Stack

Frontend

- React
- Vite
- JavaScript

Backend

- Python
- FastAPI
- LiteLLM

AI & Storage

- Google Gemini
- SQLite
- LiteLLM Response Cache

DevOps & Testing

- Docker
- Docker Compose
- Render
- Vercel
- Pytest

---

Key Features

1. Automatic API Key Failover

- Maintains an ordered pool of Gemini API keys.
- Automatically switches keys when requests fail.
- Handles rate limits, quota errors, authentication failures, and server errors.
- Implements a 30-second cooldown for failed keys.

2. Intelligent Response Caching

- Uses LiteLLM's built-in caching.
- Avoids unnecessary repeated LLM requests.
- Identifies cache hits and live inference separately.
- Supports in-memory and disk-based caching.

3. Persistent Conversations

- Stores conversation history in SQLite.
- Supports contextual multi-turn conversations.
- Maintains separate sessions.
- Supports per-session system prompts.

4. Request-Level Analytics

- Model identification.
- Response latency.
- Input and output token usage.
- Cache versus live inference status.

5. Failure Simulation

- Simulates API failures without exhausting real API keys.
- Demonstrates automatic fallback.
- Supports individual-key and complete-failure scenarios.

6. Additional Reliability Features

- Visual API routing trail.
- Live key-pool status panel.
- Cross-session cache replay.
- Structured error handling.
- Secure environment-based API key management.

---

System Architecture

flowchart TD
    A[React Frontend] --> B[FastAPI Backend]
    B --> C[Session Manager]
    C --> D[(SQLite Database)]
    B --> E[LiteLLM Gateway]
    E --> F{Response Cache}
    F -->|Hit| G[Cached Response]
    F -->|Miss| H[API Key Pool]
    H --> I[Gemini Key 1]
    I -->|Failure| J[Gemini Key 2]
    I -->|Success| K[Generate Response]
    J -->|Success| K
    K --> L[Save Conversation]
    L --> A
    G --> A

Request Lifecycle

1. User submits a message through the React interface.
2. FastAPI retrieves the relevant conversation history.
3. LiteLLM checks the response cache.
4. On a cache miss, the gateway attempts inference.
5. If an API key fails, the next available key is attempted.
6. The successful response and metadata are stored.
7. The frontend displays the answer and request analytics.

---

Design Decisions

API Key Management

Instead of relying on a single API key, Relay uses a sequential key pool.

- Each key is attempted individually.
- Failed requests trigger automatic fallback.
- Failed keys receive a temporary cooldown.
- If all keys fail, the backend returns a structured HTTP 503 response.

Caching Strategy

Caching is implemented through LiteLLM.

- Cache identity depends on the model and complete message list.
- Cache hits return "LLM_CACHE".
- Fresh responses return "LIVE_INFERENCE".
- Failure simulation bypasses caching.

Database Design

SQLite handles session and message persistence.

- Unique session identifiers.
- Separate user and assistant messages.
- Stored response metadata.
- Transactional conversation writes.
- Automatic database initialization.

Security

- API keys remain in environment variables.
- Credentials are never exposed in API responses.
- Configurable CORS restrictions.
- Input validation.
- Structured error responses.
- Non-root Docker containers.

---

Getting Started

Prerequisites

- Python 3.11+
- Node.js
- Docker Desktop (optional)
- At least two Gemini API keys for failover testing.

1. Clone the Repository

git clone <your-github-repository-url>
cd lyftr-chatbot

2. Configure Environment Variables

cp .env.example .env

Add your API keys:

LLM_API_KEYS=your_key_1,your_key_2

Never commit real API keys to GitHub.

3. Run with Docker

make up

Application URLs:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

To stop:

make down

4. Run Without Docker (Windows)

Start both services using:

.\start.ps1

Alternatively, start the backend and frontend separately.

Backend

cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

Frontend

cd frontend
npm install
npm run dev

---

Testing

Run the backend test suite:

cd backend
.\.venv\Scripts\python.exe -m pytest -v

Failure Simulation

Simulate a rate-limit error for the first key:

curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-H "X-Simulate-Failure: key_1=429" \
-d '{"session_id":"test1","message":"Hello Relay"}'

Cache Verification

Send identical messages using different session IDs to demonstrate cross-session cache reuse.

Complete Failure

Use the following header to simulate failure across all keys:

X-Simulate-Failure: *=429

The backend should return a structured "503" response.

---

Deployment

Relay uses:

- Vercel: React frontend hosting.
- Render: FastAPI backend hosting.

The frontend communicates with the deployed backend through "VITE_API_URL".

Backend configuration includes:

- "LLM_API_KEYS"
- "DATABASE_URL"
- "ALLOWED_ORIGINS"
- "ENABLE_FAILURE_SIMULATION"
- "CACHE_TYPE"

For persistent SQLite storage across Render restarts, configure a persistent disk.

---

Development Tools

- Visual Studio Code
- Claude — AI-assisted development and code review
- Docker Desktop
- Git & GitHub
- Pytest

---

Author

Shivansh Jha

- "LinkedIn" (https://www.linkedin.com/in/shivanshjha2509/)
- "GitHub" (https://github.com/)

---

<p align="center">
  <strong>Relay — Reliable AI. Smarter Conversations.</strong>
</p>