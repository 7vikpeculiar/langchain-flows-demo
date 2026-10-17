"""
Exercise: a DFA whose states are agents.

Machine  — even number of 1s on a binary tape.
Alphabet — {"0", "1"}
States   — EVEN (start + accepting), ODD

                    "0"
              ┌─────────────┐
              │             ▼
           ┌──────┐  "1"  ┌─────┐
     ●───▶ │ EVEN │ ────▶ │ ODD │
           └──────┘ ◀──── └─────┘
              ▲      "1"     │
              └──────────────┘  "0"

Point of the exercise
  The transition table lives in the agent's prompt (plain English).
  Python does not compute next-state. Python only:
    (a) refuses illegal events before the LLM runs
    (b) refuses illegal next-states after the LLM replies
    (c) walks the tape and scores ACCEPTED / REJECTED / FAILED

    ACCEPTED  — tape finished in an accepting state
    REJECTED  — tape finished in a non-accepting state
    FAILED    — a validator fired (bad event or hallucinated transition)

Fill in every BLANK. Run the tests at the bottom. Do not look up a
transition table in Python — the agent has to encode the logic.
"""
from dataclasses import dataclass, field

BLANK = None  # replace each BLANK with your code


# ---------------------------------------------------------------- 1. LLM
def call_llm(system_prompt: str, user_message: str) -> str:
    """BLANK 1 — call an LLM, return its raw text.

    Keep temperature at 0. The prompt will demand a single state name.
    Offline: you may hardcode a reply so the rest of the file is testable.
    """
    raise NotImplementedError


# ---------------------------------------------------------------- 2. Result
@dataclass
class Result:
    status: str  # "ACCEPTED" | "REJECTED" | "FAILED"
    final_state: str
    trace: list = field(default_factory=list)  # [(state, event, next_state), ...]
    reason: str = ""


# ---------------------------------------------------------------- 3. One state = one agent
class StateAgent:
    def __init__(
        self,
        name: str,
        rules: str,
        allowed_events: set,
        allowed_targets: set,
        accepting: bool = False,
    ):
        self.name = name
        self.rules = rules  # plain-English transition logic for THIS state
        self.allowed_events = allowed_events
        self.allowed_targets = allowed_targets
        self.accepting = accepting

    def validate_event(self, event: str) -> bool:
        """BLANK 2 — True only if `event` is in this state's alphabet."""
        return BLANK

    def validate_transition(self, proposed: str) -> bool:
        """BLANK 3 — True only if the model's answer is a legal next state.

        Normalise first (strip / upper). Models add punctuation and whitespace.
        """
        return BLANK

    def build_prompt(self) -> str:
        """BLANK 4 — system prompt for this agent.

        Must include: state name, self.rules, allowed_targets,
        and "reply with exactly one state name, nothing else".
        """
        return BLANK

    def step(self, event: str) -> str:
        """One event in, next-state name out.

        Pipeline (BLANK 5 — implement this, do not skip a validator):
            1. validate_event      → ValueError if False
            2. call_llm(prompt, event)
            3. validate_transition → ValueError if False
            4. return the (normalised) next-state name
        """
        raise NotImplementedError


# ---------------------------------------------------------------- 4. The machine
class AgentMachine:
    def __init__(self, agents: dict, start: str):
        self.agents = agents  # name → StateAgent
        self.start = start

    def run(self, tape: list) -> Result:
        """BLANK 6 — consume the tape left to right.

            current = start
            for each event:
                next = agents[current].step(event)
                record (current, event, next) on the trace
                current = next
            if a step raises ValueError → FAILED (keep the trace, store the reason)
            else ACCEPTED iff agents[current].accepting else REJECTED
        """
        raise NotImplementedError


# ---------------------------------------------------------------- 5. Wire the even-ones DFA
def build_even_ones_machine() -> AgentMachine:
    """BLANK 7 — construct the two agents.

    `rules` is the logic. Write it in English, e.g.
        "On 0 stay in EVEN. On 1 go to ODD."
    `allowed_events`  is the alphabet this state will accept.
    `allowed_targets` is the set of legal next-state names.
    """
    even = StateAgent(
        name="EVEN",
        rules=BLANK,
        allowed_events=BLANK,
        allowed_targets=BLANK,
        accepting=True,
    )
    odd = StateAgent(
        name="ODD",
        rules=BLANK,
        allowed_events=BLANK,
        allowed_targets=BLANK,
        accepting=False,
    )
    return AgentMachine({"EVEN": even, "ODD": odd}, start="EVEN")


# ---------------------------------------------------------------- 6. Spec (these are the tests)
if __name__ == "__main__":
    m = build_even_ones_machine()
    cases = [
        (["1", "1"],           "ACCEPTED"),
        (["1"],                "REJECTED"),
        ([],                   "ACCEPTED"),  # zero 1s is even
        (["0", "1", "0", "1"], "ACCEPTED"),
        (["1", "x"],           "FAILED"),    # validator must fire
    ]
    for tape, expected in cases:
        r = m.run(tape)
        mark = "PASS" if r.status == expected else "FAIL"
        print(f"{mark}  {tape!s:<22} -> {r.status:<9} {r.reason}")

    # Stretch (after the blanks work):
    #   A. Force the LLM to say "MAYBE" — transition validator must FAIL.
    #   B. Add a third state / a new symbol and watch which blanks break.
    #   C. Swap call_llm for a dict lookup; traces should match.
