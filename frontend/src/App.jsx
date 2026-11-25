import { useEffect, useRef, useState } from "react";
import { getHealth, sendChat } from "./api";

const newId = () => "s-" + Math.random().toString(36).slice(2, 10);
const SIMS = [
  { id: "", label: "Normal", hint: "Real keys, normal routing" },
  { id: "key_1=429", label: "Rate-limit key_1", hint: "key_1 returns 429" },
  { id: "key_1=500", label: "Crash key_1", hint: "key_1 returns 500" },
  { id: "key_1=429,key_2=500", label: "Fail key_1 and key_2", hint: "Falls through to key_3 if you have one" },
  { id: "*=429", label: "Fail every key", hint: "Expect a clean 503 message" },
];
const STARTERS = ["What is the capital of France?", "Explain caching to a ten-year-old.", "Give me three names for a coffee shop."];

function Route({ meta }) {
  const cached = meta.resolution_source === "LLM_CACHE";
  return (
    <div className="route" aria-label="Routing trail">
      {cached ? <span className="hop cache">Served from cache</span> : (
        <>
          {(meta.attempts || []).map((a) => <span key={a.key_id} className="hop bad">{a.key_id} failed ({a.status})</span>)}
          <span className="hop ok">{meta.key_id} answered</span>
        </>
      )}
    </div>
  );
}

function Assistant({ m }) {
  const { meta } = m;
  const cached = meta.resolution_source === "LLM_CACHE";
  return (
    <article className="msg bot" data-testid="assistant-message">
      <p className="text">{m.content}</p>
      <Route meta={meta} />
      <dl className="meta">
        <div><dt>Source</dt><dd data-testid="meta-source" className={cached ? "tag cache" : "tag live"}>{meta.resolution_source}</dd></div>
        <div><dt>Model</dt><dd data-testid="meta-model">{meta.model}</dd></div>
        <div><dt>Latency</dt><dd data-testid="meta-latency">{meta.latency_ms} ms</dd></div>
        <div><dt>Input tokens</dt><dd data-testid="meta-input-tokens">{meta.input_tokens}</dd></div>
        <div><dt>Output tokens</dt><dd data-testid="meta-output-tokens">{meta.output_tokens}</dd></div>
      </dl>
    </article>
  );
}

export default function App() {
  const [sid, setSid] = useState(newId);
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [sim, setSim] = useState("");
  const [sys, setSys] = useState("");
  const [health, setHealth] = useState(null);
  const [last, setLast] = useState(null);
  const end = useRef(null);

  const checkHealth = () => {
    getHealth()
      .then(setHealth)
      .catch((e) => setHealth(e?.status ? { down: true, error: e.message } : { down: true }));
  };

  useEffect(() => { checkHealth(); }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [msgs, busy]);

  async function submit(raw, id = sid, prior = msgs) {
    const message = raw.trim();
    if (!message || busy) return;
    setText(""); setBusy(true);
    setMsgs([...prior, { role: "user", content: message }]);
    try {
      const data = await sendChat({ session_id: id, message, system_prompt: sys.trim() || undefined, simulate: sim });
      setMsgs((m) => [...m, { role: "assistant", content: data.reply, meta: data.metadata }]);
      setLast(data.metadata);
      if (health?.down) checkHealth();
    } catch (e) {
      setMsgs((m) => [...m, { role: "error", content: e.message }]);
      if (sim) {
        const failedIds = sim.startsWith("*=")
          ? Array.from({ length: health?.keys_configured || 2 }, (_, i) => ({ key_id: `key_${i + 1}` }))
          : sim.split(",").map((p) => ({ key_id: p.split("=")[0].trim() })).filter((x) => x.key_id);
        setLast({ resolution_source: "LIVE_INFERENCE", key_id: null, attempts: failedIds });
      }
    } finally { setBusy(false); }
  }

  const reset = () => { setSid(newId()); setMsgs([]); setLast(null); };
  const replay = () => {
    const first = msgs.find((m) => m.role === "user");
    if (!first) return;
    const id = newId(); setSid(id); setLast(null);
    submit(first.content, id, []);
  };

  const n = health?.keys_configured || 0;
  const failed = new Set((last?.attempts || []).map((a) => a.key_id));
  const nodeState = (id) => (last?.resolution_source === "LLM_CACHE" ? "idle" : failed.has(id) ? "bad" : last?.key_id === id ? "ok" : "idle");

  return (
    <div className="shell">
      <header className="top">
        <div className="brand"><span className="ring" aria-hidden="true" /><h1>Relay</h1><span className="by">by Lyftr AI</span></div>
        <div className="actions">
          {msgs.some((m) => m.role === "user") && <button className="ghost" onClick={replay} disabled={busy} title="Resends your first message in a fresh session. A cache hit shows up immediately.">Replay first message in new chat</button>}
          <button className="ghost" onClick={reset}>New chat</button>
        </div>
      </header>

      <main className="chat">
        <div className="scroll" role="log" aria-live="polite">
          {msgs.length === 0 && (
            <section className="empty">
              <h2>Ask anything. Watch how it gets answered.</h2>
              <p>Every reply shows its source, model, latency and token cost. Use the control panel to break keys on purpose and see the failover happen.</p>
              <div className="starters">{STARTERS.map((s) => <button key={s} className="chip" onClick={() => submit(s)}>{s}</button>)}</div>
            </section>
          )}
          {msgs.map((m, i) => m.role === "assistant" ? <Assistant key={i} m={m} /> :
            m.role === "error" ? <p key={i} className="msg err" role="alert">{m.content}</p> :
            <p key={i} className="msg me">{m.content}</p>)}
          {busy && <p className="msg bot typing" aria-label="Thinking"><i /><i /><i /></p>}
          <div ref={end} />
        </div>
        <div className="composer">
          <textarea data-testid="chat-input" rows={1} value={text} placeholder="Type a message. Enter sends, Shift+Enter adds a line."
            maxLength={4000} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(text); } }} />
          <button data-testid="send-button" className="send" onClick={() => submit(text)} disabled={busy || !text.trim()}>Send</button>
        </div>
      </main>

      <aside className="panel">
        <section>
          <h3>Key pool</h3>
          {health?.down ? (
            <div className="note">
              <p style={{ margin: "0 0 8px" }}>{health.error || "Backend unreachable (check server or wait for cold start)."}</p>
              <button className="ghost" onClick={checkHealth}>Retry</button>
            </div>
          ) : (
            <div className="keys">
              {Array.from({ length: n }, (_, i) => `key_${i + 1}`).map((id) => <div key={id} className={`key ${nodeState(id)}`}><b>{id}</b><span>{{ ok: "answered", bad: "failed", idle: "standing by" }[nodeState(id)]}</span></div>)}
              <div className={`key cache ${last?.resolution_source === "LLM_CACHE" ? "ok" : "idle"}`}><b>cache</b><span>{last?.resolution_source === "LLM_CACHE" ? "answered" : "ready"}</span></div>
            </div>
          )}
        </section>
        <section>
          <h3>Failure simulator</h3>
          <p className="note">Applies to your next messages only. The backend must have simulation enabled.</p>
          <div className="sims" role="radiogroup">
            {SIMS.map((s) => <button key={s.label} role="radio" aria-checked={sim === s.id} className={`sim ${sim === s.id ? "on" : ""}`} onClick={() => setSim(s.id)}><b>{s.label}</b><span>{s.hint}</span></button>)}
          </div>
        </section>
        <section>
          <h3>System prompt</h3>
          <textarea data-testid="system-prompt-input" className="sys" rows={3} value={sys} onChange={(e) => setSys(e.target.value)} placeholder="Optional. Changes how the assistant behaves in this session." />
        </section>
        <p className="note sid">Session {sid}</p>
      </aside>
    </div>
  );
}
