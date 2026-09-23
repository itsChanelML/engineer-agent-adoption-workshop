# Engineer Agent Adoption Workshop
### Build Your First Tool-Calling Agent with Claude

A 90-minute hands-on workshop that takes a working engineer from "never
called a tool through an LLM API" to a working, resilient agent — built
from scratch, no framework, four progressive steps.

**Part of a three-piece portfolio on technical instruction:** [AirClaude](https://github.com/itsChanelML/airclaude) (build it) · **Engineer Agent Adoption Workshop** (this repo — teach it) · [Instructor Coaching Toolkit](https://github.com/itsChanelML/instructor-coaching-toolkit) (coach the instructor)

**Who this is for:** software engineers who are comfortable reading and
writing Python but have never built anything agentic — no prior LLM API or
tool-calling experience assumed. Think a new-hire enablement session, an
internal "getting started with agents" workshop, or a conference/meetup
talk aimed at engineers, not a general audience and not non-technical
learners. (If you're looking for the version of this idea built for
classroom teachers instead of engineers, that's a separate, unrelated
project: [teacher-ai-adoption](https://github.com/itsChanelML/teacher-ai-adoption).)

**Why this exists:** this is a portfolio piece built alongside
[AirClaude](https://github.com/itsChanelML/airclaude) — AirClaude demonstrates that I can build a
production-shaped agent on the Claude Developer Platform; this workshop
demonstrates that I can teach someone else to build one, with real
materials (a lab, a facilitator guide, timing data) rather than a slide
deck alone. See also
[instructor-coaching-toolkit](https://github.com/itsChanelML/instructor-coaching-toolkit),
which coaches an instructor delivering *this* workshop.

**Materials:**
- [`LAB.md`](LAB.md) — the participant-facing lab guide
- [`FACILITATOR_GUIDE.md`](FACILITATOR_GUIDE.md) — timing, common mistakes per step, how to unblock people live, how to adapt for different audiences and group sizes
- `starter/` + `solution/` — four progressive Python scripts, each with a `TODO`-marked gap and a filled-in reference version
- `common/` — the shared tool registry (three tools over a small bug-triage CSV) and environment loader

---

## What the four steps cover

| Step | New concept | File |
|---|---|---|
| 1 | The raw shape of a tool call — nothing runs until *your* code runs it | `step1_first_tool_call.py` |
| 2 | The actual loop: call → run → respond → repeat until done | `step2_agent_loop.py` |
| 3 | A registry of tools the model chooses from and chains, in an order you don't specify | `step3_multi_tool_registry.py` |
| 4 | Resilience: RETRY (the model's mistake, recoverable) vs. ESCALATE (the data's problem, not recoverable by trying again) | `step4_error_handling.py` |

Every step is tested end-to-end against the live Claude API — the exact
expected output for each is documented in both `LAB.md` (for participants)
and `FACILITATOR_GUIDE.md` (for spot-checking a room full of screens).

---

## Quick start

```bash
pip3 install -r requirements.txt
cp .env.example .env   # then paste in your ANTHROPIC_API_KEY

python3 solution/step1_first_tool_call.py
python3 solution/step2_agent_loop.py
python3 solution/step3_multi_tool_registry.py
python3 solution/step4_error_handling.py
python3 solution/step4_error_handling.py --break-registry
python3 solution/step4_error_handling.py --break-data
```

To actually work the lab rather than just read the solutions, start from
`starter/step1_first_tool_call.py` and follow `LAB.md`.

---

## About

Built by **Chanel Power** — Senior ML Engineer, Startup Advisor and Founder
of [Mentor Me Collective](https://mentormecollective.org)

- GitHub: [@itsChanelML](https://github.com/itsChanelML)
- LinkedIn: [Chanel Power](https://linkedin.com/in/powerc1)
- Community: [mentormecollective.org](https://mentormecollective.org)
