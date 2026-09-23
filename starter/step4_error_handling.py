#!/usr/bin/env python3
"""
Step 4 — Making it resilient
-------------------------------
Same loop as step 3. Two things break a naive version of this agent, and
this step fixes both:

  1. RETRY  — the model asks for a tool that doesn't exist (a typo, a
     hallucinated name, or — as here — a tool you deliberately pulled out
     of the registry). Feed the mistake back as a tool_result instead of
     crashing, and the model corrects itself on the next turn.

  2. ESCALATE — the *data* is broken (a required column got renamed
     upstream). No amount of retrying fixes that. The loop has to
     recognize ESCALATE and stop cleanly with a diagnosis, not a
     stack trace three tool calls later.

Run:
  python3 step4_error_handling.py                  # normal run
  python3 step4_error_handling.py --break-data      # ESCALATE beat
  python3 step4_error_handling.py --break-registry  # RETRY beat
"""

import argparse, inspect, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.env import get_api_key, get_model, data_file
from common.tools import TOOL_REGISTRY, TOOL_SCHEMAS, AgentStatus

import anthropic

MAX_TURNS = 8


def invoke_tool(name: str, args: dict, registry: dict):
    fn = registry[name]
    input_model = list(inspect.signature(fn).parameters.values())[0].annotation
    return fn(input_model(**args))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--break-data", action="store_true",
                        help="Use the broken CSV (severity renamed to priority) -> ESCALATE")
    parser.add_argument("--break-registry", action="store_true",
                        help="Remove draft_triage_note from the registry but keep its schema -> RETRY")
    args = parser.parse_args()

    registry = dict(TOOL_REGISTRY)
    if args.break_registry:
        del registry["draft_triage_note"]
        print("[setup] draft_triage_note removed from the registry (still in TOOL_SCHEMAS) — RETRY beat active\n")

    data_name = "bugs_broken.csv" if args.break_data else "bugs_clean.csv"
    if args.break_data:
        print("[setup] Using bugs_broken.csv — 'severity' renamed to 'priority' — ESCALATE beat active\n")

    client = anthropic.Anthropic(api_key=get_api_key())
    fp = str(data_file(data_name))

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

            # TODO(4a): `registry` may be missing a tool that TOOL_SCHEMAS
            # still advertises (see --break-registry above). If tu.name
            # isn't in `registry`, print "RETRY: No such tool: ..." and
            # append a tool_result with is_error=True and a message listing
            # list(registry) as the available tools — then `continue` to
            # the next tool_use. Do NOT call invoke_tool in this branch.
            #
            # (Until you add this check, --break-registry will raise a
            # KeyError below instead of demonstrating a graceful RETRY —
            # that crash IS the motivating example. Fix it by adding the
            # guard, not by changing invoke_tool.)

            result = invoke_tool(tu.name, tu.input, registry)
            called.append(tu.name)
            print(f"    {result.status.value}: {result.message}")

            # TODO(4b): If result.status == AgentStatus.ESCALATE, this is not
            # recoverable by retrying — print the reason and `return` out of
            # main() entirely instead of continuing the loop. (Compare: the
            # RETRY branch above uses `continue`, not `return` — RETRY means
            # "the model can fix this," ESCALATE means "a human has to.")

            tool_results.append({
                "type": "tool_result", "tool_use_id": tu.id,
                "content": result.model_dump_json(),
            })

        messages.append({"role": "user", "content": tool_results})

    print("Gave up after MAX_TURNS without a final answer.")


if __name__ == "__main__":
    main()
