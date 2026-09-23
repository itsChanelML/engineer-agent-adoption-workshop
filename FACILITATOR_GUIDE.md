# Facilitator Guide — Build Your First Tool-Calling Agent with Claude

A 90-minute hands-on session. This guide is for whoever is running it — it
assumes you've read `LAB.md` and worked through `solution/` yourself at
least once.

---

## At a glance

| | |
|---|---|
| **Format** | Hands-on lab, individual or pairs, live troubleshooting |
| **Duration** | 90 minutes |
| **Audience** | Comfortable reading/writing Python; no prior agent or LLM tool-use experience assumed |
| **Group size** | Tested for 1 facilitator : up to ~20 participants with one floating helper. Above that, recruit a second helper — see "Scaling up," below |
| **Prerequisites** | Laptop, Python 3.9+, an Anthropic API key (get one free — no billing needed for the token volume this lab uses) |

**Learning objectives.** By the end, participants can:
1. Explain what a `tool_use` content block is and why nothing runs until
   *their* code executes it.
2. Write the request/execute/respond loop from scratch, without a framework.
3. Explain why a fixed pipeline and an agent choosing its own tool order are
   different things, and when each is appropriate.
4. Distinguish a RETRY-shaped failure (the model's mistake, recoverable)
   from an ESCALATE-shaped one (the data's problem, not recoverable by
   trying again) — and say why conflating them makes agents flaky.

---

## Before the session

Send this at least 2 days ahead so setup friction doesn't eat lab time:

> Before the workshop, please:
> 1. Install Python 3.9+ if you don't have it.
> 2. Get a free Anthropic API key: console.anthropic.com/settings/keys
> 3. Clone [repo link] and run `pip3 install -r requirements.txt`
> 4. Run `python3 -c "from common.env import get_api_key; get_api_key()"` —
>    if it prints nothing, you're set. If it errors, follow the message.
>
> If any of this fails, come 10 minutes early and we'll fix it before we start.

**Your own pre-flight**, done once shortly before the session starts:
- Run all four `solution/` scripts yourself against a fresh key — confirm
  `claude-sonnet-5` is still the right default model id (check `common/env.py`
  if Anthropic has shipped a newer one since this was written) and that
  nothing in the API has changed shape.
- Have `solution/` open in a second window so you can diff against a stuck
  participant's screen in seconds instead of re-deriving the fix live.

---

## Timing (90 minutes)

| Time | Segment |
|---|---|
| 0:00–0:08 | Intro: what an agent loop actually is (a few slides), today's shape, no framework magic |
| 0:08–0:15 | Setup check — everyone runs the sanity check command live; fix stragglers now, not later |
| 0:15–0:30 | **Step 1** — first tool call |
| 0:30–0:50 | **Step 2** — the agent loop |
| 0:50–0:65 | **Step 3** — multi-tool registry |
| 0:65–0:82 | **Step 4** — RETRY vs ESCALATE |
| 0:82–0:90 | Wrap-up, stretch goal pointer, Q&A |

This assumes most people keep pace. Step 2 is where time actually gets lost
(see below) — protect its budget by trimming step 1's discussion if you're
running behind, not step 2's.

---

## Step-by-step notes

### Step 1 (15 min)
**What to watch for:** people trying to "fix" the `thinking` block they see
in the output, thinking it's an error. It isn't — say so proactively before
anyone asks, it saves several repeated questions.

**Common mistake:** forgetting `.value` on `result.status` (an enum, not a
string) and getting `AgentStatus.SUCCESS` printed instead of `SUCCESS`. Not
wrong, just ugly — worth a 10-second aside on why `AgentResult` uses an enum
here (self-documenting call sites) rather than a bare string.

**Discussion prompt while people finish:** "Why doesn't Claude just run the
tool itself?" — good opening into why tool execution has to stay in your
code: sandboxing, auth, side effects, and the model not actually having
hands.

### Step 2 (20 min) — the one that eats time
**This is where the session lives or dies on pacing.** The two things that
actually trip people up:

1. **Forgetting to append the assistant turn (2a) before checking for
   tool_use blocks.** If `messages` never grows, the second API call
   repeats the first one verbatim and the loop never terminates correctly.
   Symptom: it looks like it's "stuck" repeating the same tool call.
2. **One `tool_result` per message instead of bundling every tool_use from
   a turn into one message (2c).** With only one tool active in step 2 this
   usually still works by accident — call it out anyway, because step 3
   breaks immediately if this habit isn't fixed now, when it's harder to
   see why.

**How to unblock fast:** ask them to print `len(messages)` at the top of
each loop iteration. If it's not growing by 2 each turn (assistant + tool
results), that's the bug, before you even look at their code.

### Step 3 (15 min)
**What usually goes smoothly:** the registry dispatch itself — most people
get `invoke_tool` right quickly since it's the same pattern from steps 1–2,
generalized.

**What to highlight live:** run it twice in front of the room. The tool
*call order* Claude picks is usually stable, but ask "would it still be
correct if it called `draft_triage_note` before `find_overdue_bugs`?" — no,
because it needs the breach data first — and yet nothing in your code
enforces that order. The model is inferring the dependency from the goal
text alone. That's the concept this whole step exists to land.

### Step 4 (17 min)
**Sequence matters here — do `--break-registry` before `--break-data`.**
RETRY is the gentler failure (the loop keeps going) and primes people for
why ESCALATE needs to be a hard stop instead of "just retry harder."

**The question to ask before anyone writes code:** "What's actually
different about these two failures?" Get the room to articulate
*whose fault it is* (the model's malformed request vs. the world's broken
data) before they write the `if`/`elif` — the code is trivial once that
distinction is clear, and rote once it isn't.

**Common mistake:** using `continue` for the ESCALATE branch (copy-pasted
from the RETRY branch above it). Ask what happens next if you do that —
walk them to noticing the loop just keeps calling tools against data it
already knows is broken.

---

## Wrap-up (8 min)

Point at `common/tools.py`'s docstring on the SUCCESS/RETRY/ESCALATE
contract and mention this is the same contract a real production pipeline
(AirClaude — link it) uses at a larger scale: six tools instead of three,
context-window trimming, self-hydrating tools that re-read from source
instead of trusting echoed history. This lab is that system's skeleton with
the flesh removed so it fits in 90 minutes — say so explicitly, it's a
credible answer to "does this actually scale?"

If anyone finishes all four steps early, point them at the stretch goal in
`LAB.md` rather than letting them sit idle.

---

## Adapting

**Running long?** Cut step 1's discussion time, not step 2's — step 2 is
where the actual conceptual work happens. Step 1 can be a fast "run it, look
at the block, move on" if needed.

**More experienced audience?** Skip straight to step 3 as the starting
point and use steps 1–2 only as narrated context ("here's what that
registry is hiding"). Spend the reclaimed time going deeper on step 4 —
e.g., have them add a fourth tool and a new failure mode of their own
design.

**Scaling up (50+ participants):** you cannot debug everyone's `messages`
list individually. Pre-empt the two step 2 mistakes above explicitly in your
slides *before* people start typing, and rely on peer debugging (pair
people up) rather than 1:1 facilitator time — plan for a helper per ~15-20
participants if you have the headcount.

---

## Quick-reference: expected output per step

Use this to eyeball whether a participant's run is correct without reading
their whole screen.

- **Step 1:** `SUCCESS`, 11 breaches, Priya Nair with 7.
- **Step 2:** 2 turns, ends mentioning **auth** as the top component (4 breaches).
- **Step 3:** all 3 tools called; triage note is for **Priya Nair** (7 bugs).
- **Step 4 normal:** same as step 3.
- **Step 4 `--break-registry`:** `RETRY` printed for `draft_triage_note`,
  loop finishes anyway with a text answer that says the note couldn't be drafted.
- **Step 4 `--break-data`:** `ESCALATE` on the very first tool call,
  process halts immediately with the renamed-column diagnosis.
