# LangChain flows — live demo scripts

Standalone demos for **Part 2: LangChain flows** (12 slides) plus a break slide. Snippets are distilled from the Agentic-AI-Systems workshop repo: LangGraph hello graph, chain workflow, `with_structured_output`, and the evaluator–optimizer loop.

One running example: a support ticket for **order #4821**.

## Slides → scripts

See [SLIDES.md](./SLIDES.md) for talking points and diagrams.

| Demo | Command |
|---|---|
| Step 1 — single node | `python scripts/01_single_node.py` |
| Step 2 — chain | `python scripts/02_chain.py` |
| Why structured output | `python scripts/03_structured_why.py` |
| Pydantic schema | `python scripts/04_structured_schema.py` |
| JSON between nodes + tools | `python scripts/05_structured_between_nodes.py` |
| Step 3 — loop | `python scripts/06_loop.py` |
| Recap | `python scripts/07_recap.py` |

`01_single_node.py` needs no API key. The rest call OpenAI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set OPENAI_API_KEY
```

Run from the repo root so `scripts/common.py` imports cleanly:

```bash
PYTHONPATH=scripts python scripts/02_chain.py
```

Or:

```bash
cd scripts && python 02_chain.py
```

## Live-demo tips

1. Keep `.env` loaded; don’t paste keys into the terminal.
2. `01` first (no network) to show the graph shape.
3. `03` then `04` back-to-back so “prompted JSON” vs “schema JSON” is obvious.
4. `06` is the longest (up to 3 generate/evaluate turns).
