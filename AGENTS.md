# AGENTS.md

## Anti-loop rules (all agents)

These prevent second-guessing spirals. They apply to every agent working in this repo.

1. **Decide once.** Form a plan, then execute it. Do not re-derive the plan mid-task.
2. **Tool output is truth.** A passing test, a grep result, a file read — trust it. Do not re-run or re-read to "confirm" something already confirmed in this session.
3. **One interpretation per ambiguity.** Pick the most reasonable reading and go. Ask at most one clarifying question, before starting — never re-litigate requirements mid-task.
4. **Failure means change, not repeat.** An approach that failed twice gets a different approach, not a third retry. Never oscillate between two variants of the same fix.
5. **No review loops.** Review your own diff once. Do not re-read it, re-order it, or "polish" it after it works. Done beats perfect.
6. **No hedging in output.** State the action taken, then move on. Do not list alternatives you considered and rejected, or ask permission for steps already in the plan.
7. **Scope lock.** Only touch what the task names. Spot an unrelated issue? Note it in one line, do not fix it, do not investigate it.
8. **Stop when the goal is met.** Task complete = required behavior verified once. Extra verification passes, extra refactors, extra tests = scope creep, not diligence.

## Verification floor

Run the relevant check **once** before claiming done (test, build, or manual repro). One run is the floor and the ceiling — pass or fail, act on that single result.
