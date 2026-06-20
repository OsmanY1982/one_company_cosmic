"""
cron.jobs — In-memory cron job store and scheduling utilities.

Stores jobs in a module-level dict. Functions are called by cronjob_tools.py.
"""

import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# ── In-memory job store ────────────────────────────────────────────────────
_jobs: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _next_run_from_schedule(schedule: dict) -> Optional[str]:
    """Compute next_run_at ISO timestamp from parsed schedule dict."""
    now = datetime.now()
    interval = schedule.get("interval_seconds")
    if interval:
        return (now + timedelta(seconds=interval)).strftime("%Y-%m-%dT%H:%M:%S")
    # For cron expressions, approximate to next minute boundary
    return (now + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")


# ── Schedule parser ────────────────────────────────────────────────────────

_CRON_FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]

_HUMAN_MONTHS = {
    "1": "Jan", "2": "Feb", "3": "Mar", "4": "Apr", "5": "May", "6": "Jun",
    "7": "Jul", "8": "Aug", "9": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}
_HUMAN_DOW = {
    "0": "Sun", "1": "Mon", "2": "Tue", "3": "Wed",
    "4": "Thu", "5": "Fri", "6": "Sat", "7": "Sun",
}

_INTERVAL_RE = re.compile(
    r"^\s*(?:every\s+)?(\d+)\s*(s|sec|second|m|min|minute|h|hr|hour|d|day|w|week)s?\s*$",
    re.IGNORECASE,
)

_CRON_RE = re.compile(
    r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$"
)


def parse_schedule(schedule: str) -> Dict[str, Any]:
    """Parse a schedule string into a structured dict.

    Supports:
      - Interval strings: '30m', 'every 2h', '1d', '10s'
      - Cron expressions: '0 9 * * *', '*/5 * * * *'
      - ISO timestamp (treated as one-shot)

    Returns dict with at least 'display' and 'raw' keys.
    """
    raw = schedule.strip()

    result: Dict[str, Any] = {
        "raw": raw,
        "display": raw,
        "type": "unknown",
    }

    # Try interval
    m = _INTERVAL_RE.match(raw)
    if m:
        value = int(m.group(1))
        unit = m.group(2).lower()[0]
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        seconds = value * multipliers.get(unit, 60)

        unit_labels = {"s": "second", "m": "minute", "h": "hour", "d": "day", "w": "week"}
        label = unit_labels.get(unit, "minute")
        plural = "s" if value != 1 else ""

        result["type"] = "interval"
        result["interval_seconds"] = seconds
        result["display"] = f"every {value} {label}{plural}"
        return result

    # Try 5-field cron
    m = _CRON_RE.match(raw)
    if m:
        fields = list(m.groups())
        parts = []
        for i, field in enumerate(fields):
            if field == "*":
                continue
            if "/" in field:
                freq = field.split("/")[1]
                parts.append(f"every {freq} {_CRON_FIELD_NAMES[i]}(s)")
            else:
                parts.append(f"{_CRON_FIELD_NAMES[i]}={field}")
        display = "cron: " + (", ".join(parts) if parts else "every minute")
        result["type"] = "cron"
        result["fields"] = fields
        result["display"] = display
        return result

    # Fallback: treat as raw
    return result


# ── Job CRUD ───────────────────────────────────────────────────────────────

def create_job(
    prompt: str = "",
    schedule: str = "",
    name: Optional[str] = None,
    repeat: Optional[int] = None,
    deliver: Optional[str] = None,
    origin: Optional[Dict[str, Any]] = None,
    skills: Optional[List[str]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    script: Optional[str] = None,
    context_from: Optional[Any] = None,
    enabled_toolsets: Optional[List[str]] = None,
    workdir: Optional[str] = None,
    no_agent: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new cron job and store it in memory."""
    job_id = str(uuid.uuid4())[:8]
    schedule_info = parse_schedule(schedule) if schedule else {"display": schedule, "raw": schedule}
    now = _now_iso()

    job: Dict[str, Any] = {
        "id": job_id,
        "name": name or (prompt[:50] if prompt else (skills[0] if skills else f"job-{job_id}")),
        "prompt": prompt,
        "schedule": schedule_info,
        "schedule_display": schedule_info.get("display", schedule),
        "repeat": {"times": repeat, "completed": 0},
        "deliver": deliver or "local",
        "origin": origin,
        "skill": skills[0] if skills else None,
        "skills": skills or [],
        "model": model,
        "provider": provider,
        "base_url": base_url,
        "script": script,
        "context_from": context_from,
        "enabled_toolsets": enabled_toolsets,
        "workdir": workdir,
        "no_agent": no_agent,
        "enabled": True,
        "state": "scheduled",
        "next_run_at": _next_run_from_schedule(schedule_info),
        "last_run_at": None,
        "last_status": None,
        "last_delivery_error": None,
        "paused_at": None,
        "paused_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    _jobs[job_id] = job
    return dict(job)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a job by ID."""
    return dict(_jobs[job_id]) if job_id in _jobs else None


def list_jobs(include_disabled: bool = False) -> List[Dict[str, Any]]:
    """Return all jobs, optionally including disabled ones."""
    result = []
    for job in _jobs.values():
        if include_disabled or job.get("enabled", True):
            result.append(dict(job))
    return result


def update_job(job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update fields of an existing job. Returns the updated job dict."""
    job = _jobs.get(job_id)
    if not job:
        raise KeyError(f"Job '{job_id}' not found")

    if "schedule" in updates:
        schedule_info = updates["schedule"]
        if isinstance(schedule_info, dict):
            job["schedule"] = schedule_info
            job["schedule_display"] = schedule_info.get("display", job.get("schedule_display"))
            job["next_run_at"] = _next_run_from_schedule(schedule_info)

    for field in (
        "prompt", "name", "deliver", "skill", "skills", "model", "provider",
        "base_url", "script", "context_from", "enabled_toolsets", "workdir",
        "no_agent", "repeat",
    ):
        if field in updates:
            job[field] = updates[field]

    if "state" in updates:
        job["state"] = updates["state"]
    if "enabled" in updates:
        job["enabled"] = updates["enabled"]

    job["updated_at"] = _now_iso()
    return dict(job)


def pause_job(job_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Pause a job."""
    job = _jobs.get(job_id)
    if not job:
        raise KeyError(f"Job '{job_id}' not found")
    job["enabled"] = False
    job["state"] = "paused"
    job["paused_at"] = _now_iso()
    job["paused_reason"] = reason
    job["updated_at"] = _now_iso()
    return dict(job)


def resume_job(job_id: str) -> Dict[str, Any]:
    """Resume a paused job."""
    job = _jobs.get(job_id)
    if not job:
        raise KeyError(f"Job '{job_id}' not found")
    job["enabled"] = True
    job["state"] = "scheduled"
    job["paused_at"] = None
    job["paused_reason"] = None
    job["next_run_at"] = _next_run_from_schedule(job.get("schedule", {}))
    job["updated_at"] = _now_iso()
    return dict(job)


def remove_job(job_id: str) -> bool:
    """Remove a job from the store. Returns True if it existed."""
    if job_id in _jobs:
        del _jobs[job_id]
        return True
    return False


def trigger_job(job_id: str) -> Dict[str, Any]:
    """Manually trigger a job run now."""
    job = _jobs.get(job_id)
    if not job:
        raise KeyError(f"Job '{job_id}' not found")
    job["last_run_at"] = _now_iso()
    job["last_status"] = "triggered"
    job["updated_at"] = _now_iso()
    # Reschedule next run
    job["next_run_at"] = _next_run_from_schedule(job.get("schedule", {}))
    return dict(job)
