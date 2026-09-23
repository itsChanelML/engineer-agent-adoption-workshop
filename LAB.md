# Lab Guide — Build Your First Tool-Calling Agent with Claude

Welcome! Over the next four steps you'll build up a real (small) agent from
nothing: one raw tool call → a working loop → multiple tools the model
chooses between → an agent that survives things going wrong.

Every step lives in `starter/stepN_*.py` with one or more `TODO` markers.
If you get stuck, `solution/stepN_*.py` is the same file, filled in — try
not to peek until you've actually tried, that's where the learning is.

---

## Before you start

1. **Python 3.9+** and pip.
2. An Anthropic API key — get one free at
   [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys).
3. From this directory:

   ```bash
   pip3 install -r requirements.txt
   cp .env.example .env
   # open .env and paste your key in place of your_anthropic_api_key_here
   ```

4. Sanity check:

   ```bash
   python3 -c "from common.env import get_api_key; get_api_key(); print('key looks good')"
   ```

If that prints an error instead of "key looks good," read the message — it
tells you exactly what's wrong (missing key, still the placeholder, or
doesn't start with `sk-ant-`).

---

## Step 1 — Your first tool call

**File:** `starter/step1_first_tool_call.py`

**Goal:** see, with your own eyes, what Claude actually sends back when it
wants to call a tool. No loop, no framework — one request, one response.

Run it as-is first:
```bash
python3 starter/step1_first_tool_call.py
```
It'll print the raw response content blocks, then hit `NotImplementedError`
at the `TODO(1)` — that's your cue to fill it in.

**What you're looking for:** a `tool_use` block with a `name` and an `input`
dict. That's Claude asking you — not telling you — to run something. Nothing
executes on Anthropic's side; **your code** runs the tool.

**You'll also see a `thinking` block** in the output — that's the model's
reasoning before it decided to call a tool. You can ignore it for this
exercise; it's neither text nor a tool call, just extra context.

**Checkpoint — expected output once TODO(1) is filled in:**
```
status : SUCCESS
message: 11 bug(s) have breached their SLA window. Priya Nair has the most, with 7.
```

---

## Step 2 — The agent loop

**File:** `starter/step2_agent_loop.py`

**Goal:** turn the one-shot exchange from step 1 into an actual loop:
call → run whatever tool was requested → send the result back → repeat
until Claude stops asking for tools.

Three things to build, marked `TODO(2a)`, `(2b)`, `(2c)`:
- **2a** — append Claude's own response to the running `messages` list, so
  the next call has full context. (Content blocks need `.model_dump()` to
  become plain dicts.)
- **2b** — recognize "no more tool_use blocks" as "done," print the final
  text, and stop.
- **2c** — run the tool call(s) from this turn and send every result back
  as **one** user message with a `tool_result` block per tool call.

**The one rule that trips people up:** every `tool_use` from a turn needs a
matching `tool_result` in the very next message, all bundled together. Two
tool calls in one turn means two `tool_result` blocks in one user message —
not two separate messages.

**Checkpoint:** it should take 2 turns — one to call the tool, one to
answer in prose — and end with something like *"...the auth component has
the most, with 4 overdue bugs."*

---

## Step 3 — A registry Claude chooses from

**File:** `starter/step3_multi_tool_registry.py`

**Goal:** generalize from "one hardcoded tool" to "however many tools exist,
dispatched by name" — and hand Claude a goal that needs more than one of
them, in an order you don't specify.

Two spots to fill in:
- **`invoke_tool()` (TODO 3a)** — given a tool name and a dict of arguments,
  look the function up in `TOOL_REGISTRY`, find its Pydantic input model
  (the type annotation on its first parameter), and call it.
- **The per-tool_use handling (TODO 3b)** — call `invoke_tool`, print the
  result, and build its `tool_result`.

**Watch the order it picks.** The goal asks for three things but doesn't say
which order — that's the model's call, not your pipeline's. Run it a couple
of times; the order is usually stable but the *reasoning* for it is the
model's own.

**Checkpoint:** all three tools get called, ending in a triage note for
whichever assignee has the most overdue bugs (should be Priya Nair, with 7).

---

## Step 4 — Making it resilient

**File:** `starter/step4_error_handling.py`

**Goal:** two specific failure modes, and why they need *different*
handling.

- **`--break-registry` → RETRY.** One tool gets removed from the registry
  but Claude still sees its schema, so it will ask for it. **TODO(4a):**
  when the requested name isn't in `registry`, send back an error
  `tool_result` (not a crash) and `continue` the loop — the model gets
  another turn to adapt.
- **`--break-data` → ESCALATE.** The CSV has `severity` renamed to
  `priority`. No retry fixes a renamed column. **TODO(4b):** when a tool
  returns `AgentStatus.ESCALATE`, print the reason and `return` — stop the
  loop entirely, don't feed it back and hope.

Run all three modes once you're done:
```bash
python3 starter/step4_error_handling.py                  # normal
python3 starter/step4_error_handling.py --break-registry  # RETRY
python3 starter/step4_error_handling.py --break-data      # ESCALATE
```

**Why two different reactions to "a tool call didn't work"?** RETRY means
the *arguments or the request* were wrong — the model caused it and the
model can fix it. ESCALATE means the *situation* is wrong — the data itself
is broken, and no amount of the model trying again changes that. Conflating
the two is exactly what makes agent demos flaky: retrying forever on a
problem retrying can't fix.

---

## If you finish early — stretch goal

Every tool result here is small enough to send back to the model in full.
Real data usually isn't. Open `common/tools.py` and look at how
`find_overdue_bugs` returns a full breach list in `data["breaches"]` — for
24 rows that's harmless, but imagine 3,000. Try writing a `trim_for_history`
function that strips `data` down to just the fields the *next* tool call
actually needs before it goes into `messages`, the way AirClaude's
`tools/airclaw_tools.py` does (`trim_for_history`, at the bottom of that
file) — same idea, at production scale.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ANTHROPIC_API_KEY is not set` | You haven't run `cp .env.example .env`, or forgot to paste your key in |
| `doesn't look right (expected sk-ant-...)` | Copied a truncated key, or grabbed the wrong value | 
| `ModuleNotFoundError: No module named 'anthropic'` | `pip3 install -r requirements.txt` |
| Loop runs forever / hits `MAX_TURNS` | Usually a bug in how `tool_result` blocks are built — check every `tool_use.id` has exactly one matching `tool_result` in the very next message |
| `KeyError` on a tool name | You're on step 3/4 and `invoke_tool` isn't checking `TOOL_REGISTRY` before calling — see TODO(3a) |
