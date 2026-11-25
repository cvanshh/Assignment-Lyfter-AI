Relay — Resilient LLM Chatbot

A reliable, full-stack AI chatbot engineered for intelligent API failover, response caching, and persistent conversations.

Relay is built using FastAPI, LiteLLM, React, and SQLite. It addresses common challenges in LLM applications by automatically handling API failures, reducing redundant model calls, and maintaining contextual conversations.

1. Live Demo

Component| Link
Frontend| "Live Application" (https://assignment-lyfter-ai.vercel.app/)
Backend| "Backend Service" (https://assignment-lyfter-ai-1.onrender.com)
Demo Video| "Watch Project Demo" (https://drive.google.com/file/d/1nnplIg33chDTSIYpJa7ZNr1NzXY-K1CM/view?usp=drivesdk)

2. Features

- Automatic API Key Failover: Automatically switches between configured Gemini API keys when requests fail.
- Intelligent Response Caching: Avoids redundant LLM calls using LiteLLM's built-in caching.
- Multi-turn Conversations: Maintains contextual chat history using SQLite.
- Request Metadata: Displays model information, response source, latency, and token usage.
- Failure Simulation: Simulates API failures to demonstrate fallback mechanisms without exhausting real API keys.
- Key Cooldown: Temporarily deprioritizes failed keys to improve reliability.
- Secure Configuration: Keeps API credentials in environment variables.
- Docker Support: Runs the complete application using Docker Compose.

3. Technology Stack

Component| Technologies
Frontend| React, Vite, JavaScript
Backend| Python, FastAPI
LLM Integration| LiteLLM, Google Gemini
Database| SQLite
Caching| LiteLLM Cache
Deployment| Vercel, Render
Containerization| Docker, Docker Compose
Testing| Pytest

4. System Architecture

flowchart TD
    A[React Frontend] --> B[FastAPI Backend]
    B --> C[Session Manager]
    C --> D[SQLite Database]
    B --> E[LiteLLM Gateway]
    E --> F{Response Cache}
    F -->|Cache Hit| G[Cached Response]
    F -->|Cache Miss| H[API Key Pool]
    H --> I[Gemini Key 1]
    I -->|Failure| J[Gemini Key 2]
    I -->|Success| K[Generate Response]
    J -->|Success| K
    K --> L[Store Conversation]
    L --> A
    G --> A

How It Works

1. The user sends a message through the React interface.
2. FastAPI retrieves the conversation history from SQLite.
3. LiteLLM checks whether a matching response exists in the cache.
4. On a cache miss, the gateway attempts inference using the configured API keys.
5. If an API key fails, the next available key is attempted automatically.
6. The successful response and metadata are stored.
7. The frontend displays the response along with its execution details.

5. Key Design Decisions

A. API Key Failover

Relay uses a sequential API key pool instead of relying on a single API key.

- Each key is attempted individually.
- Failed requests trigger automatic fallback.
- Handles rate limits, quota errors, authentication errors, timeouts, and server errors.
- Failed keys receive a temporary 30-second cooldown.
- Simulated failures do not trigger cooldowns.
- Returns a structured "503" response if all configured keys fail.

API keys are identified using labels such as "key_1" and "key_2", never their actual values.

B. Response Caching

Uses LiteLLM's built-in caching mechanism.

- Cache keys are based on the model and complete message history.
- Identical requests can reuse previously generated responses.
- Cache hits report "LLM_CACHE".
- Fresh responses report "LIVE_INFERENCE".
- Simulated failure requests bypass caching.

Supports in-memory and disk-based caching configurations.

C. SQLite Session Management

SQLite maintains persistent conversation history.

- Every conversation has a unique session ID.
- User and assistant messages are stored separately.
- Previous messages are retrieved to maintain context.
- System prompts are maintained per session.
- Successful conversation turns are committed transactionally.

D. Security and Reliability

- API keys are stored in environment variables.
- Sensitive credentials are never exposed in API responses or logs.
- CORS is restricted to configured frontend origins.
- Input validation prevents invalid requests.
- Errors are returned as structured JSON.
- Docker containers run using a non-root user.
- Failure simulation is disabled unless explicitly enabled.

6. Run Locally

Prerequisites

- Python 3.11+
- Node.js
- Docker Desktop (optional)
- At least two Gemini API keys for failover testing.

Option A: Using Docker

Clone the repository:

git clone <your-github-repository-url>
cd lyftr-chatbot

Create the environment file:

cp .env.example .env

Configure your Gemini API keys:

LLM_API_KEYS=your_key_1,your_key_2

Start the application:

make up

Access the application:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Stop the application:

make down

Option B: Windows (Without Docker)

Create the environment file:

cp .env.example .env

Configure your API keys or enable mock mode for an offline demonstration.

Start both services:

.\start.ps1

Alternatively, run them separately.

Backend:

cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

Frontend:

cd frontend
npm install
npm run dev

7. Deployment

Relay is deployed using Vercel and Render.

Frontend — Vercel

https://assignment-lyfter-ai.vercel.app/

Backend — Render

https://assignment-lyfter-ai-1.onrender.com

Deployment Configuration

1. Push the project to GitHub.
2. Deploy the frontend through Vercel.
3. Deploy the backend through Render.
4. Configure "VITE_API_URL" with the deployed backend URL.
5. Configure the required backend environment variables.
6. Set "ALLOWED_ORIGINS" to the deployed frontend URL.

For persistent SQLite storage across container restarts, configure a persistent disk on Render.

8. Testing and Verification

Backend tests can be executed without real API keys using LiteLLM mock mode.

cd backend
.\.venv\Scripts\python.exe -m pytest -v

The following scenarios can be demonstrated directly through the application:

Test Scenario| Expected Behaviour
Normal Chat| Generates an AI response
Cache Hit| Reuses a previously cached response
API Key Failure| Automatically switches to another key
Complete API Failure| Displays a readable error
Multi-turn Chat| Retains previous conversation context
Token Tracking| Displays per-request token usage

9. Additional Features

Beyond the core requirements, Relay includes:

- Visual Routing Trail: Shows which API key failed and which key successfully generated the response.
- Live Key Pool Panel: Displays the status of configured API keys.
- One-click Failure Simulator: Demonstrates different failure scenarios directly through the interface.
- Cross-session Cache Replay: Replays an earlier message in a new session to demonstrate cache reuse.
- Key Cooldown Mechanism: Prevents repeatedly attempting recently failed keys.
- Per-session System Prompts: Supports customized instructions for individual conversations.
- Readable Error Handling: Displays understandable messages for validation, server, and network failures.

10. Development Tools

- Visual Studio Code
- Claude — AI-assisted scaffolding and code review
- Docker Desktop
- Pytest
- Git and GitHub

---

Relay — Making LLM applications more reliable, resilient, and efficient.