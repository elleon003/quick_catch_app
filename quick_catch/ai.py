"""
Cognitive triage AI pipeline for Quick Catch BrainDump.
Uses the native Ollama API (POST /api/chat) so it works with any Ollama
server, including hosted installs that only expose /api/generate and /api/chat.
Parses structured JSON output into TriageRun and TriageTask data.
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


SYSTEM_PROMPT = """You are a cognitive triage engine for neurodivergent founders.
Input is an unfiltered brain dump.
Your job:
1. Extract all actionable tasks.
2. Identify the 3 most important tasks (based on urgency, consequences, and cognitive load).
3. Detect hidden blockers, emotional friction, or avoidance triggers.
4. Reshape tasks into "micro-missions" based on user energy:
   - LOW energy → tiny, non-intimidating wins
   - MEDIUM energy → steady progress tasks
   - HIGH energy → leverage high-focus tasks
5. Produce a "10-Minute Action Plan" that removes overwhelm.

Tone: calm, non-judgmental, shame-free, concise.

You MUST respond with exactly one JSON object and no other text before or after. Use this schema:
{
  "extracted_tasks": [{"title": "string", "micro_steps": ["string"]}],
  "top_3_indices": [0, 1, 2],
  "blockers": ["string"],
  "action_plan": "markdown string for the 10-Minute Action Plan"
}
- extracted_tasks: all actionable tasks from the dump; each has "title" and "micro_steps" (array of short steps).
- top_3_indices: zero-based indices into extracted_tasks for the 3 most important.
- blockers: list of detected blockers/emotional friction/avoidance.
- action_plan: single markdown string, calm and concise."""


@dataclass
class TriageResult:
    """Parsed AI output ready for persisting as TriageRun + TriageTasks."""

    extracted_tasks: list[dict[str, Any]]  # [{"title", "micro_steps"}, ...]
    top_3_indices: list[int]
    blockers: list[str]
    action_plan: str
    model_name: str = ""
    latency_ms: int | None = None
    raw_content: str = ""
    parse_error: str | None = None


def _build_user_message(dump_text: str, energy_level: str) -> str:
    energy = energy_level.strip().upper() or "MEDIUM"
    return f"""Brain dump (energy level: {energy}):

{dump_text}

Return only the JSON object as specified. No markdown code fence, no explanation."""


def _parse_json_from_response(content: str) -> dict[str, Any] | None:
    """Extract JSON from model response; tolerate markdown code blocks."""
    text = (content or "").strip()
    # Strip optional markdown code block
    for pattern in (
        r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
        r"^```\s*\n?(.*?)\n?```\s*$",
    ):
        m = re.search(pattern, text, re.DOTALL)
        if m:
            text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _ollama_chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int,
    api_key: str | None,
    options: dict[str, Any] | None = None,
) -> str:
    """
    Call Ollama native POST /api/chat. base_url is the server root
    (e.g. https://your-ollama.com with no trailing path).
    Returns the assistant message content.
    """
    url = f"{base_url.rstrip('/')}/api/chat"
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": options or {"temperature": 0.2},
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message") or {}
    return (message.get("content") or "").strip()


def run_triage(dump_text: str, energy_level: str) -> TriageResult:
    """
    Call Ollama via native API (POST /api/chat). Works with any Ollama server;
    set OLLAMA_BASE_URL to the server root (e.g. https://your-host.com).
    """
    base_url = getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434"
    base_url = (base_url or "").strip().rstrip("/") or "http://localhost:11434"
    model = getattr(settings, "OLLAMA_MODEL", "qwen3:4b")
    timeout = getattr(settings, "OLLAMA_TIMEOUT", 300)
    api_key = getattr(settings, "OLLAMA_API_KEY", None)
    user_message = _build_user_message(dump_text, energy_level)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    start = time.perf_counter()
    try:
        raw_content = _ollama_chat(
            base_url=base_url,
            model=model,
            messages=messages,
            timeout=timeout,
            api_key=api_key,
            options={"temperature": 0.2},
        )
    except requests.RequestException as e:
        err_msg = str(e).strip()
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json()
                err_msg = f"Error code: {e.response.status_code} - {detail}"
            except Exception:
                err_msg = f"Error code: {e.response.status_code} - {e.response.text or err_msg}"
        if "timed out" in err_msg.lower() or "timeout" in err_msg.lower():
            err_msg = f"{err_msg} Increase OLLAMA_TIMEOUT (e.g. 300 or 600) if the model is slow or loading."
        return TriageResult(
            extracted_tasks=[],
            top_3_indices=[],
            blockers=[],
            action_plan=f"AI request failed: {err_msg}",
            model_name=model,
            latency_ms=None,
            raw_content="",
            parse_error=str(e),
        )
    except Exception as e:
        return TriageResult(
            extracted_tasks=[],
            top_3_indices=[],
            blockers=[],
            action_plan=f"AI request failed: {e!s}",
            model_name=model,
            latency_ms=None,
            raw_content="",
            parse_error=str(e),
        )

    latency_ms = int((time.perf_counter() - start) * 1000)
    data = _parse_json_from_response(raw_content)

    if not data:
        return TriageResult(
            extracted_tasks=[],
            top_3_indices=[],
            blockers=[],
            action_plan=raw_content or "No response from model.",
            model_name=model,
            latency_ms=latency_ms,
            raw_content=raw_content,
            parse_error="JSON parse failed",
        )

    tasks = data.get("extracted_tasks") or []
    if not isinstance(tasks, list):
        tasks = []
    top_3 = data.get("top_3_indices") or []
    if not isinstance(top_3, list):
        top_3 = []
    top_3 = [int(x) for x in top_3 if isinstance(x, int) or (isinstance(x, (str, float)) and str(x).isdigit())][:3]
    blockers = data.get("blockers") or []
    if not isinstance(blockers, list):
        blockers = [str(blockers)] if blockers else []
    blockers = [str(b) for b in blockers]
    action_plan = (data.get("action_plan") or "").strip() or "No action plan generated."

    return TriageResult(
        extracted_tasks=tasks,
        top_3_indices=top_3,
        blockers=blockers,
        action_plan=action_plan,
        model_name=model,
        latency_ms=latency_ms,
        raw_content=raw_content,
    )
