"""
RepoMind FastAPI server — receives GitHub webhooks and runs agents.
"""
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from orchestrator import RepoMindOrchestrator

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="RepoMind", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"])

orchestrator = RepoMindOrchestrator()
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def verify_signature(payload: bytes, sig: str) -> bool:
    if not WEBHOOK_SECRET or not sig:
        return True
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


@app.get("/")
async def health():
    return {"status": "RepoMind online ✅",
            "agents": list(orchestrator.list_agents().keys())}


@app.post("/webhook/github")
async def github_webhook(request: Request, bg: BackgroundTasks):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, sig):
        raise HTTPException(401, "Invalid webhook signature")

    event = request.headers.get("X-GitHub-Event", "unknown")
    payload = json.loads(body)
    logger.info(f"Webhook: {event} from {payload.get('repository',{}).get('full_name','?')}")

    bg.add_task(orchestrator.process_event, event, payload)
    return JSONResponse({"status": "accepted", "event": event})


@app.get("/agents")
async def list_agents():
    return orchestrator.list_agents()


@app.get("/memory/{agent_name}")
async def get_memory(agent_name: str):
    return orchestrator.get_memory(agent_name)


@app.get("/logs")
async def get_logs():
    log_path = Path(__file__).parent.parent / "agents/orchestrator/memory/runtime/dailylog.md"
    try:
        return {"log": log_path.read_text()}
    except FileNotFoundError:
        return {"log": "No log yet."}


@app.post("/test/pr")
async def test_pr(request: Request):
    """Manual test endpoint — simulate a PR event."""
    body = await request.json()
    result = orchestrator.process_event("pull_request", {
        "action": "opened",
        "pull_request": {
            "number": body.get("number", 1),
            "title": body.get("title", "Test PR"),
            "body": body.get("body", ""),
            "user": {"login": "test-user"},
            "base": {"ref": "main"},
            "changed_files": 3,
            "additions": 50,
            "deletions": 5,
            "diff_url": body.get("diff_url", ""),
        },
        "repository": {"full_name": body.get("repo", "test/repo")},
    })
    return {"result": result}


@app.post("/test/issue")
async def test_issue(request: Request):
    """Manual test endpoint — simulate an issue event."""
    body = await request.json()
    result = orchestrator.process_event("issues", {
        "action": "opened",
        "issue": {
            "number": body.get("number", 1),
            "title": body.get("title", "Test Issue"),
            "body": body.get("body", ""),
            "user": {"login": "reporter"},
            "labels": [],
        },
        "repository": {"full_name": body.get("repo", "test/repo")},
    })
    return {"result": result}
