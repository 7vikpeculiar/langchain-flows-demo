# AI agents tutorial (LangChain + Ollama)

Small scripts for a college workshop. `scripts/common.py` defines `ChatGptModel()` — slides say ChatGPT, it runs **Ollama** locally. In the LangGraph scripts, set `LOG_GRAPH = True` at the top of the file for per-node traces.

## Setup

Use the **testingo** pyenv env (or any env with the packages below):

```bash
pyenv activate testingo
pip install -r requirements.txt
ollama pull llama3.1:8b   # must match scripts/common.py
```

Run from the repo root:

```bash
python scripts/01_chat_model.py
python scripts/02_bind_tools.py
python scripts/03_model_chaining_inefficient.py
python scripts/03_model_chaining_graph.py
python scripts/04_loop_review.py
python scripts/05_memory.py first
python scripts/05_memory.py followup
python scripts/05_memory.py reset    # clear tickets.db
python scripts/06_validators.py      # Agno post_hooks + @validator helpers
```

| Script | What it shows |
|--------|----------------|
| `01_chat_model.py` | `ChatGptModel()` + `invoke` |
| `02_bind_tools.py` | `@tool` + `bind_tools` |
| `03_model_chaining_inefficient.py` | Two `invoke` calls — triage → reply |
| `03_model_chaining_graph.py` | Same chain as LangGraph nodes |
| `04_loop_review.py` | AI review loop until approved (writes `scripts/output/loop_review.png`) |
| `05_memory.py` | Same loop + SQLite memory across runs (`scripts/output/memory_graph.png`) |
| `06_validators.py` | Agno agent + Python validators (`post_hooks`, no LLM reviewer) |
| `02_bind_tools_underlying.py` | Manual tool loop (how agents run tools) |
| `take_home.py` | Take-home exercise (DFA with agents) |
