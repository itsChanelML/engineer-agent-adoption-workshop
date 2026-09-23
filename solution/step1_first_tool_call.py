#!/usr/bin/env python3
"""
Step 1 — Your first tool call
------------------------------
No loop yet. One request, one look at exactly what comes back. This is the
raw material every agent loop is built from — steps 2-4 are all about what
you do with this shape, in a loop, more than once.

Run:
  python3 step1_first_tool_call.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.env import get_api_key, get_model, data_file
from common.tools import find_overdue_bugs, FindOverdueBugsInput

import anthropic

# Just the one tool for this step — Claude's native tool schema shape:
# name + description + input_schema (JSON Schema).
TOOLS = [{
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
}]


def main():
    client = anthropic.Anthropic(api_key=get_api_key())
    fp = str(data_file("bugs_clean.csv"))

    response = client.messages.create(
        model=get_model(),
        max_tokens=512,
        tools=TOOLS,
        messages=[{
            "role": "user",
            "content": f"Find all overdue bugs. The data file is at {fp}.",
        }],
    )

    print("── Raw response content blocks ──")
    for block in response.content:
        print(f"  type: {block.type}")
        if block.type == "tool_use":
            print(f"    id    : {block.id}")
            print(f"    name  : {block.name}")
            print(f"    input : {block.input}")
        elif block.type == "text":
            print(f"    text  : {block.text!r}")
    print(f"  stop_reason: {response.stop_reason}")

    # Claude only ASKED for the tool call — nothing has actually run yet.
    # Pull the tool_use block out and run it ourselves.
    tool_use = next(b for b in response.content if b.type == "tool_use")
    result = find_overdue_bugs(FindOverdueBugsInput(**tool_use.input))

    print("\n── Running the tool Claude asked for ──")
    print(f"  status : {result.status.value}")
    print(f"  message: {result.message}")


if __name__ == "__main__":
    main()
