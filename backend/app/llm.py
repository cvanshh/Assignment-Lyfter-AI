"""LiteLLM gateway: key pool, failover, response cache. Keys are never logged or returned."""
import logging
import os
import time

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
import litellm
from .config import settings

log = logging.getLogger("chatbot")

litellm.drop_params = True
litellm.telemetry = False

class AllProvidersFailed(Exception):
    def __init__(self, attempts: list[dict]):
        self.attempts = attempts

class SimulatedFailure(Exception):
    def __init__(self, status: int):
        self.status_code = status

def setup_cache() -> None:
    if settings.cache_type == "disk":
        os.makedirs(settings.cache_dir, exist_ok=True)
        litellm.cache = litellm.Cache(type="disk", disk_cache_dir=settings.cache_dir)
    else:
        litellm.cache = litellm.Cache(type="local")

def parse_simulation(header: str | None) -> dict[str, int]:
    """'key_1=429,key_2=500' or '*=429' -> {'key_1': 429, ...}. Bad pairs are ignored."""
    out: dict[str, int] = {}
    for part in (header or "").split(","):
        k, _, v = part.strip().partition("=")
        if k and v.strip() in ("429", "500", "502", "503"):
            out[k.strip()] = int(v)
    return out

_cooldown_until: dict[str, float] = {}

def _ordered_keys() -> list[tuple[str, str]]:
    keys = [(f"key_{i + 1}", k) for i, k in enumerate(settings.keys)]
    now = time.monotonic()
    ready = [p for p in keys if _cooldown_until.get(p[0], 0) <= now]
    cooling = [p for p in keys if p not in ready]
    return ready + cooling  # cooled-down keys go last, never excluded

async def complete(messages: list[dict], simulate: dict[str, int]) -> dict:
    attempts: list[dict] = []
    use_cache = not simulate  # simulated requests must return a fresh, real answer
    for key_id, key in _ordered_keys():
        status = simulate.get(key_id) or simulate.get("*")
        try:
            if status:
                raise SimulatedFailure(status)
            extra = {"mock_response": f"Mock reply to: {messages[-1]['content']}"} if settings.mock else {}
            resp = await litellm.acompletion(model=settings.model, messages=messages, api_key=key,
                                             caching=use_cache, num_retries=0, timeout=30, temperature=0.3, **extra)
            reply = (resp.choices[0].message.content or "").strip()
            if not reply:
                raise ValueError("empty completion")
            hit = bool((getattr(resp, "_hidden_params", None) or {}).get("cache_hit"))
            usage = getattr(resp, "usage", None)
            in_tok = int(getattr(usage, "prompt_tokens", 0) or 0)
            out_tok = int(getattr(usage, "completion_tokens", 0) or 0)
            return {
                "reply": reply, "model": settings.model, "cache_hit": hit,
                "input_tokens": in_tok, "output_tokens": out_tok,
                "key_id": None if hit else key_id, "fallback_attempts": 0 if hit else len(attempts),
                "attempts": attempts,
            }
        except Exception as e:  # 429, quota, 5xx, auth, timeouts: all mean "try the next key"
            err_status = getattr(e, "status_code", None) or "error"
            log.warning("Provider %s failed (%s): %s", key_id, err_status, type(e).__name__)
            attempts.append({"key_id": key_id, "status": err_status})
            if not status:
                _cooldown_until[key_id] = time.monotonic() + settings.cooldown
    raise AllProvidersFailed(attempts)
