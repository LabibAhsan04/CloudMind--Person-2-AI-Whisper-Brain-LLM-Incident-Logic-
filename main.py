from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

import logging
import json
import os
import random
import re
from collections import deque, Counter
from typing import List, Set, Optional

import httpx
from dotenv import load_dotenv

# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(title="CloudMind - AI Whisper (Person 2)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()

# ============================================================
# SIMPLE KEY GATE (ENCRYPTION / ACCESS CONTROL)
# ============================================================

SHARED_KEY = os.getenv("CLOUDMIND_INGEST_KEY", "change-this-key")


def require_key(
    key: Optional[str] = Query(default=None),
    x_key: Optional[str] = Header(default=None, convert_underscores=False),
    authorization: Optional[str] = Header(default=None),
):
    """
    Only allow requests that provide the correct shared key.
    - via ?key=...
    - or X-Key header
    - or Authorization: Bearer <key>
    """
    provided = key or x_key

    if not provided and authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1]

    if provided != SHARED_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing key")


# ============================================================
# OPENROUTER CONFIG (FREE MODELS + FAILOVER)
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-r1:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-4b-it:free",
    "microsoft/phi-4-reasoning:free",
]

logging.info(f"AI enabled: {bool(OPENROUTER_API_KEY)}")
logging.info(f"Model failover order: {OPENROUTER_MODELS}")

# ============================================================
# MODELS
# ============================================================

class StatusInput(BaseModel):
    service_name: str
    metrics: dict   # e.g. {"cpu": 95, "latency": 2.5, "errors": 20, "queue": 120}


class BatchInput(BaseModel):
    items: List[StatusInput]


# ============================================================
# MEMORY + WEBSOCKETS
# ============================================================

HISTORY: deque = deque(maxlen=200)
CLIENTS: Set[WebSocket] = set()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    CLIENTS.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        CLIENTS.discard(ws)


async def _broadcast(obj: dict):
    """Send JSON to all connected websocket clients."""
    text = json.dumps(obj)
    dead = []
    for c in list(CLIENTS):
        try:
            await c.send_text(text)
        except Exception:
            dead.append(c)
    for d in dead:
        CLIENTS.discard(d)


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    """Redirect to Swagger docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {
        "ok": True,
        "ai_enabled": bool(OPENROUTER_API_KEY),
        "key_protected": SHARED_KEY != "change-this-key",
    }


@app.get("/ai-debug")
def ai_debug():
    """Quick check that AI key / models are loaded."""
    return {
        "ai_enabled": bool(OPENROUTER_API_KEY),
        "models": OPENROUTER_MODELS,
    }


@app.get("/recent")
def recent(limit: int = 20) -> List[dict]:
    return list(HISTORY)[-limit:]


@app.get("/stats")
def stats(limit: int = 100):
    items = list(HISTORY)[-limit:]
    counts = Counter(i.get("emotion") for i in items)
    total = sum(counts.values()) or 1
    percent = {
        k: round((counts.get(k, 0) / total) * 100, 1)
        for k in ("calm", "stressed", "panic")
    }
    return {
        "window": min(limit, len(items)),
        "counts": counts,
        "percent": percent,
    }


@app.get("/services")
def services(limit: int = 50) -> List[dict]:
    """
    Return the latest status per service_name,
    so frontends that call /services don't 404.
    """
    items = list(HISTORY)[-limit:]

    latest_by_service = {}
    for item in items:
        name = item.get("service_name")
        if not name:
            continue
        latest_by_service[name] = {
            "service_name": name,
            "metrics": item.get("metrics", {}),
            "emotion": item.get("emotion"),
            "severity": item.get("severity"),
            "problem": item.get("problem"),
            "solution": item.get("solution"),
            "source": item.get("source"),
        }

    return list(latest_by_service.values())


# ============================================================
# AI: ASK OPENROUTER FOR PROBLEM + SOLUTION
# ============================================================

async def generate_problem_and_solution(service_name: str, metrics: dict):
    """
    Ask OpenRouter: given service name + metrics,
    return (problem, solution). Uses multiple free models with failover.
    """
    if not OPENROUTER_API_KEY:
        return "", ""

    user_text = (
        f"Service: {service_name}\n"
        f"Metrics: {json.dumps(metrics)}\n\n"
        "You are a reliability engineer.\n"
        "Be VERY short and practical.\n"
        "Format exactly like this:\n"
        "Problem: <one short sentence>\n"
        "Solution: <one or two short sentences or bullet points>\n"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    for model in OPENROUTER_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Be concise. Separate Problem and Solution clearly.",
                },
                {"role": "user", "content": user_text},
            ],
            "max_tokens": 160,
            "temperature": 0.2,
        }

        logging.info(f"Trying OpenRouter model={model}")
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(OPENROUTER_URL, headers=headers, json=payload)

            if r.status_code != 200:
                logging.warning(f"{model} failed: {r.status_code}")
                continue

            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                continue

            problem_match = re.search(r"(?i)problem[:\-]\s*(.+)", content)
            solution_match = re.search(r"(?i)solution[:\-]\s*(.+)", content, re.S)

            problem = problem_match.group(1).strip() if problem_match else ""
            solution = solution_match.group(1).strip() if solution_match else ""

            if problem or solution:
                logging.info(f"✅ Model {model} succeeded.")
                return problem, solution

        except Exception as e:
            logging.warning(f"Error with model {model}: {e}")
            continue

    return "", ""


# ============================================================
# MAIN ROUTES (SINGLE SERVICE)
# ============================================================

@app.post("/whisper-ai", dependencies=[Depends(require_key)])
async def whisper_ai(payload: StatusInput):
    """
    Process ONE service:
    - classify mood (calm / stressed / panic)
    - ask AI for problem + solution (if possible)
    """
    mood = decide_mood(payload.metrics, payload.service_name)
    severity = {"calm": "info", "stressed": "warn", "panic": "critical"}[mood]

    problem, solution = await generate_problem_and_solution(
        payload.service_name, payload.metrics
    )

    if problem or solution:
        source = "ai_problem_and_solution"
    else:
        problem = f"{payload.service_name} is showing {mood} conditions."
        solution = make_message(payload.service_name, mood, payload.metrics)
        source = "rules_fallback"

    obj = {
        "service_name": payload.service_name,
        "metrics": payload.metrics,
        "emotion": mood,
        "severity": severity,
        "problem": problem,
        "solution": solution,
        "source": source,
    }

    HISTORY.append(obj)
    await _broadcast(obj)

    return obj


# ============================================================
# BATCH ROUTE (MANY SERVICES AT ONCE)
# ============================================================

@app.post("/whisper-ai-batch", dependencies=[Depends(require_key)])
async def whisper_ai_batch(body: BatchInput):
    """
    Process MANY services at once (e.g., all 5 microservices):
    - decides mood for each
    - calls AI for each (with same failover logic)
    """
    results: List[dict] = []

    for idx, item in enumerate(body.items, start=1):
        try:
            mood = decide_mood(item.metrics, item.service_name)
            severity = {"calm": "info", "stressed": "warn", "panic": "critical"}[mood]

            problem, solution = await generate_problem_and_solution(
                item.service_name, item.metrics
            )

            if problem or solution:
                source = "ai_problem_and_solution"
            else:
                problem = f"{item.service_name} is showing {mood} conditions."
                solution = make_message(item.service_name, mood, item.metrics)
                source = "rules_fallback"

            obj = {
                "service_name": item.service_name,
                "metrics": item.metrics,
                "emotion": mood,
                "severity": severity,
                "problem": problem,
                "solution": solution,
                "source": source,
            }

            HISTORY.append(obj)
            await _broadcast(obj)
            results.append(obj)

        except Exception as e:
            results.append({
                "service_name": item.service_name,
                "emotion": "unknown",
                "severity": "unknown",
                "problem": "",
                "solution": "",
                "source": "error",
                "error": f"item {idx} failed: {type(e).__name__}: {e}",
            })

    return {
        "count": len(results),
        "results": results,
    }


# ============================================================
# LOGIC (MOOD + EMOJI MESSAGE)
# ============================================================

def decide_mood(m: dict, service_name: str) -> str:
    name = service_name.lower()
    cpu = m.get("cpu", 0)
    latency = m.get("latency", 0.0)
    errors = m.get("errors", 0)
    queue = m.get("queue", 0)
    hit_ratio = m.get("hit_ratio")
    evictions = m.get("evictions", 0)
    fail_rate = m.get("fail_rate")
    qps = m.get("qps")

    # database / fear
    if "database" in name or "db" in name or "fear" in name:
        if errors > 5 or latency > 2.0 or cpu > 90:
            return "panic"
        if latency > 1.0 or (qps and qps > 2000):
            return "stressed"
        return "calm"

    # cache / sadness
    if "cache" in name or "sadness" in name:
        if hit_ratio is not None:
            if hit_ratio < 0.60 or evictions > 500:
                return "panic"
            if hit_ratio < 0.85 or evictions > 100:
                return "stressed"
            return "calm"
        if cpu > 85 or queue > 200:
            return "stressed"
        return "calm"

    # auth / disgust
    if "auth" in name or "disgust" in name:
        if fail_rate is not None:
            if fail_rate > 0.20:
                return "panic"
            if fail_rate > 0.05:
                return "stressed"
            return "calm"
        if errors > 10:
            return "stressed"
        return "calm"

    # api / frontend / joy / anger
    if errors > 10 or cpu > 85:
        return "panic"
    if latency > 1.5 or queue > 50:
        return "stressed"
    return "calm"


def make_message(name: str, mood: str, m: dict) -> str:
    voices = {
        "Joy": {
            "calm": ["😊 Joy is smooth sailing!"],
            "stressed": ["😅 Joy’s juggling a lot—hang tight!"],
            "panic": ["⚠️ Joy’s overwhelmed—need backup!"],
        },
        "Anger": {
            "calm": ["😎 Anger is focused."],
            "stressed": ["🔥 Anger is heating up."],
            "panic": ["💥 Anger is furious—requests are exploding!"],
        },
        "Fear": {
            "calm": ["🙂 Fear is steady."],
            "stressed": ["😟 Fear is worried—too many queries."],
            "panic": ["😨 Fear is panicking—falling behind!"],
        },
        "Sadness": {
            "calm": ["🙂 Sadness is okay."],
            "stressed": ["😔 Sadness feels heavy—low cache hits."],
            "panic": ["🥶 Sadness is overwhelmed—evictions spiking!"],
        },
        "Disgust": {
            "calm": ["🙂 Disgust is selective and calm."],
            "stressed": ["🤢 Disgust is rejecting a lot—auth noisy."],
            "panic": ["🚫 Disgust is disgusted—too many bad logins!"],
        },
    }

    persona = next((p for p in voices if name.startswith(p)), None)
    if persona:
        return random.choice(voices[persona][mood])

    generic = {
        "calm": [f"✅ {name} is running smoothly."],
        "stressed": [f"⏳ {name} feels slow—load is rising."],
        "panic": [f"🔥 {name} is overloaded—errors spiking!"],
    }
    return random.choice(generic[mood])
