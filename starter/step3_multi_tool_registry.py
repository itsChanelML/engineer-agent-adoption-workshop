#!/usr/bin/env python3
"""
Step 3 — A registry Claude chooses from
------------------------------------------
Step 2 hardcoded one tool. Real agents pick from several, in whatever order
the goal requires. This step swaps the single find_overdue_bugs call for
common/tools.py's full TOOL_REGISTRY (three tools) and gives Claude a goal
that requires calling more than one of them, in an order we don't specify.

Watch which order it picks — it's the model's decision, not a hardcoded
pipeline. That's the whole point of tool calling over a fixed script.

Run:
  python3 step3_multi_tool_registry.py
"""

import inspect, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.env import get_api_key, get_model, data_file
from common.tools import TOOL_REGISTRY, TOOL_SCHEMAS

import anthropic

MAX_TURNS = 8


def invoke_tool(name: str, args: dict):
    """Look the tool up by name and call it with its typed input model."""
    # TODO(3a): Look `name` up in TOOL_REGISTRY to get the function, find its
    # first parameter's type annotation (that's the Pydantic input model —
    # see step 1/2 for the pattern), and return fn(input_model(**args)).
    #
    #   hint: list(inspect.signature(fn).parameters.values())[0].annotation
    raise NotImplementedError("Your turn — see TODO(3a) above")


def main():
    client = anthropic.Anthropic(api_key=get_api_key())
    fp = str(data_file("bugs_clean.csv"))

    messages = [{
        "role": "user",
        "content": (
            f"The bug data is at {fp}. Find all overdue bugs, summarize open "
            f"bugs by severity, and draft a triage note for whichever "
            f"assignee has the most overdue bugs. Finish with a one-sentence "
            f"summary of what you found."
        ),
    }]

    called = []

    for turn in range(1, MAX_TURNS + 1):
        response = client.messages.create(
            model=get_model(),
            max_tokens=1024,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": [b.model_dump() for b in response.content]})

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            final_text = "".join(b.text for b in response.content if b.type == "text")
            print(f"\n── Done ── (called: {' → '.join(called)})\n{final_text}")
            return

        tool_results = []
        for tu in tool_uses:
            print(f"[turn {turn}] → {tu.name}({tu.input})")

            if tu.name not in TOOL_REGISTRY:
                tool_results.append({
                    "type": "tool_result", "tool_use_id": tu.id, "is_error": True,
                    "content": f"No such tool: {tu.name}. Available: {list(TOOL_REGISTRY)}.",
                })
                continue

            # TODO(3b): Call invoke_tool(tu.name, tu.input), print its status
            # and message (and its `note` field if one comes back — see the
            # solution for the exact print pattern), append it to `called`,
            # and add a tool_result dict for it to tool_results using
            # result.model_dump_json() as the content.
            raise NotImplementedError("Your turn — see TODO(3b) above")

        messages.append({"role": "user", "content": tool_results})

    print("Gave up after MAX_TURNS without a final answer.")


if __name__ == "__main__":
    main()
