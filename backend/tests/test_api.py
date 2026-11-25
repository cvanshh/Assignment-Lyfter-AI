import uuid

def sid(): return "s-" + uuid.uuid4().hex[:8]
def post(client, session, msg, headers=None, **kw):
    return client.post("/chat", json={"session_id": session, "message": msg, **kw}, headers=headers or {})

def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "keys_configured": 2, "cache_enabled": True}

def test_live_then_cache_across_sessions(client):
    msg = "unique question " + uuid.uuid4().hex
    a = post(client, sid(), msg).json()
    b = post(client, sid(), msg).json()
    assert a["metadata"]["resolution_source"] == "LIVE_INFERENCE" and a["metadata"]["key_id"] == "key_1"
    assert b["metadata"]["resolution_source"] == "LLM_CACHE" and b["metadata"]["key_id"] is None
    assert b["metadata"]["fallback_attempts"] == 0 and a["reply"] == b["reply"]
    assert a["metadata"]["input_tokens"] == b["metadata"]["input_tokens"] > 0
    assert post(client, sid(), msg + " different").json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"

def test_multi_turn_history(client):
    s = sid()
    post(client, s, "first " + uuid.uuid4().hex)
    second = post(client, s, "second " + uuid.uuid4().hex).json()
    msgs = client.get(f"/sessions/{s}/messages").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert "metadata" in msgs[1] and "metadata" not in msgs[0]
    assert second["metadata"]["input_tokens"] > 0

def test_failover_single_key(client):
    for h in ("key_1=429", "key_1=500"):
        r = post(client, sid(), "failover " + uuid.uuid4().hex, {"X-Simulate-Failure": h})
        assert r.status_code == 200
        m = r.json()["metadata"]
        assert m["key_id"] == "key_2" and m["fallback_attempts"] == 1 and m["resolution_source"] == "LIVE_INFERENCE"

def test_all_keys_fail_503_not_stored(client):
    s = sid()
    r = post(client, s, "doomed", {"X-Simulate-Failure": "*=429"})
    assert r.status_code == 503 and r.json() == {"detail": "all providers unavailable"}
    assert client.get(f"/sessions/{s}/messages").status_code == 404

def test_validation_and_404(client):
    assert post(client, sid(), "   ").status_code == 422
    assert post(client, sid(), "x" * 4001).status_code == 422
    assert post(client, "", "hi").status_code == 422
    assert client.post("/chat", content="{bad json", headers={"content-type": "application/json"}).status_code == 422
    r = client.get("/sessions/nope/messages")
    assert r.status_code == 404 and r.json() == {"detail": "session not found"}
