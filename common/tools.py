"""
Tool registry — shared by every step, unchanged from step 1 through step 4.

Three tools over one small CSV of bug reports:

  find_overdue_bugs    — which open bugs have breached their SLA window
  summarize_by_severity — counts of open bugs by severity
  draft_triage_note    — a ready-to-send note for one assignee's overdue bugs

Same shape as production agent tooling: a typed input model per tool, and a
result contract of SUCCESS / RETRY / ESCALATE instead of a bare return value
or a raised exception. That contract is what step 4 exercises — every tool
here already speaks it, on purpose, before you need it.

  SUCCESS  — worked. `data` has the payload.
  RETRY    — the *arguments* were wrong (bad column name, typo). The model
             can fix its own inputs and call again.
  ESCALATE — the *situation* is wrong (the data itself is broken). No retry
             fixes this — a human needs to look at it.
"""

import csv
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel

REQUIRED_FIELDS = [
    "bug_id", "title", "component", "severity", "status",
    "assignee", "hours_open", "sla_hours", "sla_breach",
]


class AgentStatus(str, Enum):
    SUCCESS  = "SUCCESS"
    RETRY    = "RETRY"
    ESCALATE = "ESCALATE"


class AgentResult(BaseModel):
    status:  AgentStatus
    data:    Dict[str, Any] = {}
    message: str = ""


def _check_schema(fields: List[str]) -> str:
    """Return a diagnosis string if a required field is missing, else ''."""
    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    if not missing:
        return ""
    return (
        f"Missing required field(s): {missing}. "
        f"Fields present: {fields}. "
        f"This looks like a renamed column upstream — the pipeline can't guess "
        f"the new name, so a human needs to update REQUIRED_FIELDS or fix the "
        f"source file."
    )


# ── Input schemas ──────────────────────────────────────────────────────────────

class FindOverdueBugsInput(BaseModel):
    file_path: str
    component: str = ""   # optional filter, e.g. "api". Empty = all components.


class SummarizeBySeverityInput(BaseModel):
    file_path: str


class DraftTriageNoteInput(BaseModel):
    file_path: str
    assignee:  str


# ── Tools ──────────────────────────────────────────────────────────────────────

def find_overdue_bugs(input: FindOverdueBugsInput) -> AgentResult:
    path = Path(input.file_path)
    if not path.exists():
        return AgentResult(status=AgentStatus.ESCALATE, message=f"File not found: {input.file_path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        diagnosis = _check_schema(fields)
        if diagnosis:
            return AgentResult(status=AgentStatus.ESCALATE, message=diagnosis)
        rows = list(reader)

    breaches, by_component, by_assignee = [], defaultdict(int), defaultdict(int)
    for row in rows:
        if row.get("sla_breach", "").strip() != "YES":
            continue
        if input.component and row.get("component", "") != input.component:
            continue
        breaches.append({
            "bug_id":     row.get("bug_id", ""),
            "title":      row.get("title", ""),
            "component":  row.get("component", ""),
            "severity":   row.get("severity", ""),
            "assignee":   row.get("assignee", ""),
            "hours_open": row.get("hours_open", ""),
            "sla_hours":  row.get("sla_hours", ""),
        })
        by_component[row.get("component", "")] += 1
        by_assignee[row.get("assignee", "")]   += 1

    if not breaches:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            message="No SLA breaches found.",
            data={"breaches": [], "total": 0},
        )

    top_assignee = max(by_assignee.items(), key=lambda kv: kv[1])
    return AgentResult(
        status=AgentStatus.SUCCESS,
        message=(
            f"{len(breaches)} bug(s) have breached their SLA window. "
            f"{top_assignee[0]} has the most, with {top_assignee[1]}."
        ),
        data={
            "breaches":     breaches,
            "total":        len(breaches),
            "by_component": dict(by_component),
            "by_assignee":  dict(by_assignee),
        },
    )


def summarize_by_severity(input: SummarizeBySeverityInput) -> AgentResult:
    path = Path(input.file_path)
    if not path.exists():
        return AgentResult(status=AgentStatus.ESCALATE, message=f"File not found: {input.file_path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        diagnosis = _check_schema(fields)
        if diagnosis:
            return AgentResult(status=AgentStatus.ESCALATE, message=diagnosis)
        rows = list(reader)

    counts = defaultdict(int)
    for row in rows:
        if row.get("status", "") == "Closed":
            continue
        counts[row.get("severity", "unknown")] += 1

    if not counts:
        return AgentResult(status=AgentStatus.SUCCESS, message="No open bugs.", data={"counts": {}})

    top = max(counts.items(), key=lambda kv: kv[1])
    return AgentResult(
        status=AgentStatus.SUCCESS,
        message=f"{sum(counts.values())} open bugs. Most common severity: {top[0]} ({top[1]}).",
        data={"counts": dict(counts), "total_open": sum(counts.values())},
    )


def draft_triage_note(input: DraftTriageNoteInput) -> AgentResult:
    if not input.assignee.strip():
        return AgentResult(status=AgentStatus.RETRY, message="assignee is required and was empty.")

    path = Path(input.file_path)
    if not path.exists():
        return AgentResult(status=AgentStatus.ESCALATE, message=f"File not found: {input.file_path}")

    # Reads straight from the file rather than trusting a bug list the model
    # might pass in — same reason AirClaude's briefing tool re-reads from
    # source instead of echoing an earlier tool's output back through history.
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        diagnosis = _check_schema(fields)
        if diagnosis:
            return AgentResult(status=AgentStatus.ESCALATE, message=diagnosis)
        rows = list(reader)

    mine = [
        r for r in rows
        if r.get("assignee", "") == input.assignee and r.get("sla_breach", "").strip() == "YES"
    ]

    if not mine:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            message=f"{input.assignee} has no SLA-breached bugs.",
            data={"note": ""},
        )

    lines = [f"TRIAGE NOTE — {input.assignee}", ""]
    for b in sorted(mine, key=lambda r: float(r["hours_open"]), reverse=True):
        lines.append(
            f"  [{b['severity'].upper():8}] {b['bug_id']} — {b['title']} "
            f"({b['hours_open']}h open, SLA {b['sla_hours']}h)"
        )
    note = "\n".join(lines)

    return AgentResult(
        status=AgentStatus.SUCCESS,
        message=f"Drafted a triage note for {input.assignee} — {len(mine)} bug(s).",
        data={"note": note, "count": len(mine)},
    )


# ── Registry (used from step 3 onward) ─────────────────────────────────────────

TOOL_REGISTRY = {
    "find_overdue_bugs":     find_overdue_bugs,
    "summarize_by_severity": summarize_by_severity,
    "draft_triage_note":     draft_triage_note,
}

TOOL_SCHEMAS = [
    {
        "name": "find_overdue_bugs",
        "description": "Find open bugs that have exceeded their SLA window. Optionally filter to one component.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "component": {"type": "string", "description": "Optional filter, e.g. 'api'. Empty = all components."},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "summarize_by_severity",
        "description": "Count open bugs grouped by severity (critical/high/medium/low).",
        "input_schema": {
            "type": "object",
            "properties": {"file_path": {"type": "string"}},
            "required": ["file_path"],
        },
    },
    {
        "name": "draft_triage_note",
        "description": "Write a ready-to-send triage note listing one assignee's SLA-breached bugs, ranked by hours open.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "assignee":  {"type": "string", "description": "Exact assignee name as it appears in the data, e.g. 'Priya Nair'."},
            },
            "required": ["file_path", "assignee"],
        },
    },
]
