"""Step 6 — validators with Agno (no LLM reviewer).

Agno has no @validator decorator in the framework. It validates output with
post_hooks that raise OutputCheckError. This file defines a small @validator
helper that turns plain functions into those hooks — same idea as step 4's
review node, but attached to the agent.

    python scripts/06_validators.py
"""

from __future__ import annotations

import re
from functools import wraps
from pathlib import Path
from typing import Callable

from agno.agent import Agent
from agno.exceptions import CheckTrigger, OutputCheckError
from agno.run import RunStatus
from agno.run.agent import RunOutput
from agno.workflow import Loop, Step, Workflow

from common import ChatGptModel2

LOG = False

TICKET = (
    "Hi, this is Sathvik from Acme. My order #4321 arrived yesterday but the "
    "keyboard is missing two keys. Can I get a replacement shipped to "
    "91 Market Street by Friday? Thanks."
)

MAX_ATTEMPTS = 3
MAX_WORDS = 150
FORBIDDEN = ["guarantee", "100% sure", "full refund"]

ORDER_RE = re.compile(r"#\d+")
DEADLINE_RE = re.compile(r"\bby\s+\w+", re.I)
TICKET_MARKER = "Customer ticket:\n"

ValidatorFn = Callable[[str, str], list[str]]
_VALIDATORS: list[ValidatorFn] = []
_LAST_FEEDBACK: str = ""


def log(*args, **kwargs) -> None:
    if LOG:
        print(*args, **kwargs)


def validator(fn: ValidatorFn) -> ValidatorFn:
    """Register a draft checker; Agno runs the combined hook after each agent.run()."""

    @wraps(fn)
    def wrapper(reply: str, ticket: str) -> list[str]:
        return fn(reply, ticket)

    _VALIDATORS.append(wrapper)
    return wrapper


def _ticket_from_prompt(prompt: str) -> str:
    if TICKET_MARKER not in prompt:
        return prompt
    after = prompt.split(TICKET_MARKER, 1)[1]
    return after.split("\n\n", 1)[0].strip()


def _run_validators(run_output: RunOutput) -> None:
    global _LAST_FEEDBACK
    reply = str(run_output.content or "")
    prompt = run_output.input.input_content_string() if run_output.input else ""
    ticket = _ticket_from_prompt(prompt)

    problems: list[str] = []
    for check in _VALIDATORS:
        problems.extend(check(reply, ticket))

    if problems:
        _LAST_FEEDBACK = "FIX: " + "; ".join(problems)
        log("validators FAILED ->", _LAST_FEEDBACK)
        raise OutputCheckError(
            _LAST_FEEDBACK,
            check_trigger=CheckTrigger.OUTPUT_NOT_ALLOWED,
        )

    _LAST_FEEDBACK = ""
    log("validators APPROVED")


@validator
def order_number(reply: str, ticket: str) -> list[str]:
    problems = []
    for order in ORDER_RE.findall(ticket):
        if order not in reply:
            problems.append(f"order number {order} not mentioned")
    return problems


@validator
def deadline(reply: str, ticket: str) -> list[str]:
    match = DEADLINE_RE.search(ticket)
    if not match:
        return []
    day = match.group(0).split()[-1].lower()
    if day not in reply.lower():
        return [f"acknowledge the deadline ({match.group(0)})"]
    return []


@validator
def length(reply: str, ticket: str) -> list[str]:
    words = len(reply.split())
    if words > MAX_WORDS:
        return [f"too long ({words} words, max {MAX_WORDS})"]
    return []


@validator
def forbidden_promises(reply: str, ticket: str) -> list[str]:
    lower = reply.lower()
    return [f'remove promise: "{phrase}"' for phrase in FORBIDDEN if phrase in lower]


def build_demo_workflow(triage_agent: Agent, drafter_agent: Agent) -> Workflow:
    """Same shape as this script — used for the printed reference graph."""
    return Workflow(
        name="support_validators",
        steps=[
            Step(name="triage", agent=triage_agent),
            Loop(
                name="draft_until_valid",
                steps=[Step(name="draft_reply", agent=drafter_agent)],
                max_iterations=MAX_ATTEMPTS,
                forward_iteration_output=True,
            ),
        ],
    )


def make_agents() -> tuple[Agent, Agent]:
    model = ChatGptModel2()

    triage = Agent(
        name="Triage",
        model=model,
        instructions=[
            "Reply with one line: category (billing/shipping/defect/other) "
            "and priority (low/medium/high)."
        ],
    )

    drafter = Agent(
        name="Drafter",
        model=model,
        instructions=[
            "You are a support agent drafting short emails.",
            "You often forget to include the order number even when the ticket mentions one.",
            "Output only the email body — no meta commentary.",
        ],
        post_hooks=[_run_validators],
    )
    return triage, drafter


def draft_prompt(ticket: str, triage: str, feedback: str, previous: str) -> str:
    prompt = (
        f"{TICKET_MARKER}{ticket}\n\n"
        f"Triage:\n{triage}\n\n"
        "Draft a short, friendly support email."
    )
    if feedback:
        prompt += (
            f"\n\nPrevious draft:\n{previous}\n\n"
            f"A reviewer found these issues. Fix them:\n{feedback}"
        )
    return prompt


if __name__ == "__main__":
    triage_agent, drafter_agent = make_agents()

    triage_result = triage_agent.run(f"Customer ticket:\n{TICKET}")
    triage_line = str(triage_result.content or "").strip()
    log("triage:", triage_line)

    reply = ""
    feedback = ""
    approved = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log(f"\n── draft attempt {attempt} ──")
        prompt = draft_prompt(TICKET, triage_line, feedback, reply)
        result = drafter_agent.run(prompt)
        reply = str(result.content or "")

        if result.status == RunStatus.completed:
            approved = True
            break

        feedback = _LAST_FEEDBACK or "FIX: draft did not pass validators"
        log("retry with:", feedback)

    print("\n══ Final ══")
    print("Attempts:", attempt, "| Approved:", approved)
    print("Reply:\n", reply)
