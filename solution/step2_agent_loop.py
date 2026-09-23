#!/usr/bin/env python3
"""
Step 2 — The agent loop
------------------------
Step 1 stopped after one tool call. Real work usually takes more than one —
so this step turns that single exchange into a loop: call Claude, run
whatever tool it asked for, hand the result back, and repeat until it stops
asking for tools.

Still one tool on purpose — the loop mechanics are the new idea here, not
tool variety. Step 3 adds the other two tools.

Run:
  python3 step2_agent_loop.py
"""

import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.env import get_api_key, get_model, data_file
from common.tools import find_overdue_bugs, FindOverdueBugsInput

import anthropic

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

MAX_TURNS = 5


def main():
    client = anthropic.Anthropic(api_key=get_api_key())
    fp = str(data_file("bugs_clean.csv"))

    messages = [{
        "role": "user",
        "content": (
            f"Find all overdue bugs in {fp}, then tell me in one sentence "
            f"which component has the most."
        ),
    }]

    for turn in range(1, MAX_TURNS + 1):
        print(f"\n[turn {turn}] calling Claude…")
        response = client.messages.create(
            model=get_model(),
            max_tokens=512,
            tools=TOOLS,
            messages=messages,
        )

        # Claude's reply — whatever mix of text and tool_use blocks it
        # returned — becomes the next assistant turn in the conversation.
        messages.append({"role": "assistant", "content": [b.model_dump() for b in response.content]})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # No more tool calls — Claude is done. Print whatever text it wrote.
            final_text = "".join(b.text for b in response.content if b.type == "text")
            print(f"\n── Done ──\n{final_text}")
            return

        # Run every tool call from this turn, then send ALL the results back
        # together in one user message — Claude expects one tool_result per
        # tool_use, in the very next turn.
        tool_results = []
        for tu in tool_uses:
            print(f"  → {tu.name}({tu.input})")
            result = find_overdue_bugs(FindOverdueBugsInput(**tu.input))
            print(f"    {result.status.value}: {result.message}")
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tu.id,
                "content":     result.model_dump_json(),
            })

        messages.append({"role": "user", "content": tool_results})

    print("Gave up after MAX_TURNS without a final answer.")


if __name__ == "__main__":
    main()
