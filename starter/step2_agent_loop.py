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

        # TODO(2a): Append Claude's reply to `messages` as the next assistant
        # turn. response.content is a list of content-block objects — each
        # needs .model_dump() to become a plain dict before it can go in a
        # messages list.
        #   messages.append({"role": "assistant", "content": ...})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # TODO(2b): No more tool calls means Claude is done. Concatenate
            # every text block's .text and print it, then `return`.
            pass

        # TODO(2c): Run every tool call from this turn, building one
        # tool_result dict per call:
        #   {"type": "tool_result", "tool_use_id": tu.id, "content": <json string>}
        # Collect them in a list, then append ONE user message containing
        # all of them:
        #   messages.append({"role": "user", "content": tool_results})
        #
        # Call find_overdue_bugs(FindOverdueBugsInput(**tu.input)) for each
        # tool_use `tu`, and use result.model_dump_json() as the content.
        raise NotImplementedError("Your turn — see TODO(2a-2c) above")

    print("Gave up after MAX_TURNS without a final answer.")


if __name__ == "__main__":
    main()
