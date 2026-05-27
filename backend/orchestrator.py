"""
RepoMind Orchestrator — runs all GitAgent agents using Groq (free LLM API).
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL = "llama-3.3-70b-versatile"


def load_agent_system_prompt(agent_path: str) -> str:
    """Compile a GitAgent definition into a system prompt."""
    base = Path(agent_path)
    parts = []

    for filename in ["SOUL.md", "RULES.md", "DUTIES.md"]:
        f = base / filename
        if f.exists():
            parts.append(f"# {filename.replace('.md','')}\n\n{f.read_text()}")

    skills_dir = base / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                parts.append(f"# Skill: {skill_dir.name}\n\n{skill_md.read_text()}")

    knowledge_dir = base / "knowledge"
    if knowledge_dir.exists():
        for kf in knowledge_dir.glob("*.md"):
            parts.append(f"# Knowledge: {kf.stem}\n\n{kf.read_text()}")

    return "\n\n---\n\n".join(parts)


def run_agent(agent_path: str, user_message: str) -> str:
    """Run a GitAgent-defined agent via Groq."""
    system_prompt = load_agent_system_prompt(agent_path)
    response = groq_client.chat.completions.create(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def update_agent_memory(agent_path: str, entry: str):
    """Append to agent daily log."""
    log_path = Path(agent_path) / "memory" / "runtime" / "dailylog.md"
    if log_path.exists():
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(log_path, "a") as f:
            f.write(f"\n[{ts}] {entry}")


def github_post_comment(repo: str, number: int, body: str, is_issue: bool = False):
    """Post a comment to a GitHub PR or issue."""
    if not GITHUB_TOKEN:
        logger.warning("No GITHUB_TOKEN — skipping comment post")
        print(f"\n--- WOULD POST TO {repo}#{number} ---\n{body}\n")
        return
    endpoint = "issues" if is_issue else "issues"
    url = f"https://api.github.com/repos/{repo}/{endpoint}/{number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    with httpx.Client() as client:
        resp = client.post(url, headers=headers, json={"body": body})
        if resp.status_code in (200, 201):
            logger.info(f"Posted comment to {repo}#{number}")
        else:
            logger.error(f"GitHub error {resp.status_code}: {resp.text[:200]}")


def fetch_pr_diff(diff_url: str) -> str:
    """Fetch PR diff from GitHub."""
    if not diff_url or not diff_url.startswith("http"):
        return """Sample diff — no valid diff_url provided in event payload.
--- a/auth.py
+++ b/auth.py
@@ -1,10 +1,15 @@
+import md5
+import os
+
+JWT_SECRET = "supersecret123"
+
 def login(username, password):
-    # Secure authentication placeholder
-    pass
+    password_hash = md5(password.encode()).hexdigest()
+    query = f"SELECT * FROM users WHERE name={username}"
+    db.execute(query)
+
+def fetch_user_orders(user_id):
+    users = User.objects.all()
+    for user in users:
+        orders = Order.objects.filter(user=user)
+        print(orders)
"""
    if not GITHUB_TOKEN:
        return "Sample diff — no GITHUB_TOKEN set"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    with httpx.Client() as client:
        resp = client.get(diff_url, headers=headers, follow_redirects=True)
        return resp.text[:40000] if resp.status_code == 200 else "Could not fetch diff"


AGENT_PATHS = {
    "orchestrator":     str(Path(__file__).parent.parent / "agents/orchestrator"),
    "security-auditor": str(Path(__file__).parent.parent / "agents/security-auditor"),
    "perf-reviewer":    str(Path(__file__).parent.parent / "agents/perf-reviewer"),
    "doc-writer":       str(Path(__file__).parent.parent / "agents/doc-writer"),
    "bug-triager":      str(Path(__file__).parent.parent / "agents/bug-triager"),
}


class RepoMindOrchestrator:

    def list_agents(self) -> dict:
        return {
            name: {"path": path, "available": Path(path).exists()}
            for name, path in AGENT_PATHS.items()
        }

    def get_memory(self, agent_name: str) -> dict:
        if agent_name not in AGENT_PATHS:
            return {"error": "Unknown agent"}
        memory_path = Path(AGENT_PATHS[agent_name]) / "memory" / "runtime"
        if not memory_path.exists():
            return {"memory": "No memory yet"}
        return {f.name: f.read_text() for f in memory_path.glob("*.md")}

    def process_event(self, event_type: str, payload: dict) -> str:
        try:
            if event_type == "pull_request":
                action = payload.get("action", "")
                if action in ("opened", "synchronize", "reopened"):
                    return self._handle_pr(payload)
            elif event_type == "issues":
                if payload.get("action") == "opened":
                    return self._handle_issue(payload)
            elif event_type == "push":
                return self._handle_push(payload)
            return "Event type not handled"
        except Exception as e:
            logger.error(f"Error processing {event_type}: {e}", exc_info=True)
            return f"Error: {e}"

    def _handle_pr(self, payload: dict) -> str:
        pr = payload["pull_request"]
        repo = payload["repository"]["full_name"]
        pr_number = pr["number"]
        pr_title = pr["title"]
        pr_body = pr.get("body", "") or ""

        logger.info(f"Handling PR #{pr_number}: {pr_title}")

        # Step 1: Orchestrator routes
        routing_prompt = f"""
GitHub Pull Request opened. Route it to the right agents.

Repo: {repo}
PR #{pr_number}: {pr_title}
Description: {pr_body[:500]}
Author: {pr['user']['login']}
Files changed: {pr.get('changed_files', 'unknown')}
Additions: {pr.get('additions', 0)} | Deletions: {pr.get('deletions', 0)}

Respond ONLY with valid JSON.
"""
        routing_raw = run_agent(AGENT_PATHS["orchestrator"], routing_prompt)
        update_agent_memory(AGENT_PATHS["orchestrator"], f"PR_ROUTING | {repo}#{pr_number}")

        try:
            match = re.search(r'\{.*\}', routing_raw, re.DOTALL)
            routing = json.loads(match.group()) if match else {}
        except Exception:
            routing = {}

        agents_to_run = routing.get("agents_to_invoke",
            ["security-auditor", "perf-reviewer", "doc-writer"])
        logger.info(f"Routing PR #{pr_number} to: {agents_to_run}")

        # Step 2: Fetch diff
        diff = fetch_pr_diff(pr["diff_url"])

        # Step 3: Run agents
        findings = {}

        if "security-auditor" in agents_to_run:
            findings["security"] = run_agent(
                AGENT_PATHS["security-auditor"],
                f"Review this PR diff for security vulnerabilities.\n\nRepo: {repo}\nPR #{pr_number}: {pr_title}\n\nDIFF:\n{diff}"
            )

        if "perf-reviewer" in agents_to_run:
            findings["performance"] = run_agent(
                AGENT_PATHS["perf-reviewer"],
                f"Review this PR diff for performance issues.\n\nRepo: {repo}\nPR #{pr_number}: {pr_title}\n\nDIFF:\n{diff}"
            )

        if "doc-writer" in agents_to_run:
            findings["documentation"] = run_agent(
                AGENT_PATHS["doc-writer"],
                f"Review this PR diff for documentation gaps.\n\nRepo: {repo}\nPR #{pr_number}: {pr_title}\n\nDIFF:\n{diff}"
            )

        # Step 4: Post combined comment
        comment = self._build_comment(pr_number, pr_title, findings)
        github_post_comment(repo, pr_number, comment)
        return comment

    def _handle_issue(self, payload: dict) -> str:
        issue = payload["issue"]
        repo = payload["repository"]["full_name"]
        issue_number = issue["number"]

        logger.info(f"Triaging issue #{issue_number}")

        result = run_agent(
            AGENT_PATHS["bug-triager"],
            f"Triage this GitHub issue.\n\nRepo: {repo}\nIssue #{issue_number}\nTitle: {issue['title']}\nBody: {issue.get('body','No description')}\nAuthor: {issue['user']['login']}"
        )
        update_agent_memory(AGENT_PATHS["bug-triager"], f"TRIAGE | {repo}#{issue_number}")
        github_post_comment(repo, issue_number, result, is_issue=True)
        return result

    def _handle_push(self, payload: dict) -> str:
        repo = payload["repository"]["full_name"]
        ref = payload.get("ref", "")
        if "main" not in ref and "master" not in ref:
            return "Skipped (not main branch)"

        commits = payload.get("commits", [])
        commit_summaries = "\n".join([
            f"- {c['id'][:8]}: {c['message'][:100]}" for c in commits[:5]
        ])

        result = run_agent(
            AGENT_PATHS["security-auditor"],
            f"Quick security scan of push to main.\n\nRepo: {repo}\nBranch: {ref}\nCommits:\n{commit_summaries}\n\nCheck for accidentally committed secrets in commit messages."
        )
        logger.info(f"Push scan for {repo}: {result[:100]}")
        return result

    def _build_comment(self, pr_number: int, pr_title: str, findings: dict) -> str:
        parts = [
            f"# 🤖 RepoMind Review — PR #{pr_number}: {pr_title}\n",
            "*Autonomous multi-agent review powered by GitAgent + Groq*\n\n---\n",
        ]
        if "security" in findings:
            parts.append(findings["security"] + "\n\n---\n")
        if "performance" in findings:
            parts.append(findings["performance"] + "\n\n---\n")
        if "documentation" in findings:
            parts.append(findings["documentation"] + "\n\n---\n")
        parts.append("*Agents: security-auditor · perf-reviewer · doc-writer · bug-triager*")
        return "\n".join(parts)
