# Meal Prep Agent

An AI Agent helping you solve one of the hardest questions out there:

> "What to eat for dinner?"

Use a Telegram Bot to interact with the Agent.

## Commands

```bash
# Install dependencies
uv sync

# Run the bot
uv run python main.py

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_foo.py::test_bar

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Environment

Create a `.env` file at root. See `.env.example`.

- `ANTHROPIC_API_KEY`
- `CHROMA_HOST`
- `CHROMA_PORT`
- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `VOYAGE_API_KEY`

**Optional — Langfuse observability (omit to disable tracing):**

- `LANGFUSE_HOST` (defaults to `https://cloud.langfuse.com`)
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

**Create a `.env.test` file at root for a separated test environment.**

## Database Setup

Meal Prep Agent requires a running PostgreSQL instance. The quickest way is Docker:

```bash
docker run -d \
  --name mealprep-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mealprep \
  -p 5432:5432 \
  postgres:16
```

Then set `DATABASE_URL` in your `.env`:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mealprep"
```

Use a separate config for your tests in `.env.test` so they will be isolated since we need to reset the database after every test:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mealprep_test"
```

To stop and remove the container:

```bash
docker stop mealprep-postgres && docker rm mealprep-postgres
```

### Migrations

Meal Prep Agent uses [yoyo](https://ollycope.com/software/yoyo/latest/) for schema migrations against Postgres. Migrations run synchronously at startup before the bot begins accepting messages. No manual step required.

To add a new migration, create `migrations/NNN-migration-name.sql`. It will be applied automatically on next startup.

## Prompt Management

System prompts are versioned and stored in the `prompts` table in Postgres. This lets you update prompts without redeploying the bot — the active version for each prompt type is loaded at runtime.

There are four prompt types, one per agent node:

| Type | Used by |
| --- | --- |
| `classifier` | Intent classification |
| `plan` | Meal plan generation |
| `parse_recipe` | Recipe parsing |
| `chat` | General chat responses |

Each type has at most one active version at a time. If no active prompt is found for a type, the node falls back to its hardcoded default.

### CLI

Use `manage_prompts.py` to insert and manage prompt versions:

```bash
# Prefix the command with your DATABASE_URL.
# e.g. DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mealprep"

# Add a new prompt version (--active promotes it immediately)
DATABASE_URL=<DATABASE_URL> uv run python manage_prompts.py add \
  --type classifier \
  --version 2 \
  --file prompts/classifier_v2.txt \
  --notes "tightened parse_recipe examples" \
  --active

# List all prompts across all types
DATABASE_URL=<DATABASE_URL> uv run python manage_prompts.py list

# Promote a specific version by id
DATABASE_URL=<DATABASE_URL> uv run python manage_prompts.py activate 5
```

*Activating a version automatically deactivates all other versions of the same type.*

## Agentic Workflow (LangGraph)

The agent is built as a [LangGraph](https://langchain-ai.github.io/langgraph/) `StateGraph`. Each Telegram message is a graph invocation; nodes read and write a shared `BotState` that flows through the graph.

### State

```python
class BotState(TypedDict):
    chat_id: int
    user_message: str
    intent: ClassifiedIntent | None
    reply: str | list[str] | None
    pending_recipe: Recipe | None
```

### Graph structure

<img width="782" height="926" alt="meal-prep-agent-flowchart" src="https://github.com/user-attachments/assets/8ee6cd39-a5d3-4ac5-9207-be164109a949" />

```plaintext
START
  ↓
classify_intent
  ↓ (conditional)
  ├→ create_meal_plan → END
  ├→ parse_recipe → confirm_recipe ─┬→ save_recipe    → END
  │                  (interrupt)    └→ discard_recipe  → END
  └→ chat → END
```

### Human-in-the-loop (interrupt)

Recipe parsing is a two-turn flow. After `parse_recipe` extracts a recipe, the graph pauses at `confirm_recipe` using LangGraph's `interrupt()`. The bot sends the parsed recipe plus a confirmation prompt to the user, then halts.

On the next message, the handler checks `graph.aget_state(config).next` — if the graph is paused, it resumes via `Command(resume=user_message)` instead of starting a new invocation. The user's reply routes to either `save_recipe` (persists to DB + embeds) or `discard_recipe`.

### Checkpointing

LangGraph's `AsyncPostgresSaver` backs the checkpointer, storing graph state in the same PostgreSQL database used for recipes. Each Telegram `chat_id` maps to a LangGraph `thread_id`, giving every user an isolated, persistent conversation thread. The checkpointer is created at startup inside an `AsyncExitStack` so its connection pool is cleanly closed on shutdown.

This means graph state — including an in-progress recipe confirmation — survives bot restarts.

## RAG (Retrieval-Augmented Generation)

Meal Prep Agent uses RAG to surface relevant recipes when building a meal plan, avoiding the need to pass your entire recipe library to Claude on every request.

**How it works:**

1. **Embedding** — When a recipe is saved, its name, tags, ingredients, and cook time are embedded via [VoyageAI](https://www.voyageai.com/) (`voyage-4`) and stored in a [ChromaDB](https://www.trychroma.com/) collection named `recipes`.
2. **Reconciliation** — On startup, any recipes without embeddings are backfilled so the vector store stays in sync with the database.
3. **Retrieval** — When a meal plan is requested, a semantic search (`k=10`) is run against the vector store. The top results, combined with last week's selections for variety, form the recipe bank passed to Claude.
4. **Selection** — Claude Sonnet picks 5 weekday dinners from that bank and returns structured output (recipe IDs + rationale).

This keeps prompt size bounded and improves selection quality by giving Claude a curated, contextually relevant subset of recipes rather than an unbounded list.

## Observability (Langfuse)

Langfuse traces every LangGraph invocation when credentials are present. If the Langfuse env vars are missing or auth fails, the bot starts normally with tracing disabled — no hard dependency on the service.

**What gets traced:**

- Every graph run: node-by-node execution, latency, and total duration
- Each Claude API call: model, prompt, completion, token counts, and cost
- Prompt cache hit/miss via Anthropic's usage fields

## Design Decisions

- **Multi-model routing** — `claude-haiku-4-5` for intent classification (fast, cheap); `claude-sonnet-4-6` for meal planning and recipe parsing (capable). Cost is optimized at the routing layer, not as an afterthought.
- **Prompt caching** — All system prompts use `cache_control: ephemeral`, reducing latency and token cost on repeated calls.
- **Forced tool schema** — The classifier uses a constrained tool definition to guarantee structured JSON output; no free-text parsing or regex needed.
- **Conversation history** — SQLite-backed message store scoped per user, injected as context into the chat workflow.
- **Atomic writes** — Storage uses `.tmp` → `os.replace()` + `asyncio.Lock` to prevent partial writes under concurrent requests.

## Roadmap

### Evals

- Offline eval harness: given a fixed recipe bank + user message, assert the selected meals satisfy constraints (variety, calorie targets, user preferences)
- Classification accuracy tracking: log `(input, predicted_intent, ground_truth)` triples and run a nightly eval job
- LLM-as-judge: use Claude to score meal plan quality across dimensions like balance and variety

### Multi-modal

- Accept food photos via Telegram; use Claude's vision input to parse a recipe from a photo or menu screenshot

### Human Feedback Loop

- After each meal plan, prompt the user to rate it (👍/👎); store ratings and bias future selection accordingly
- Surface low-rated meals as negative examples in the selection prompt

### Guardrails & Safety

- Output validation on `save_recipe`: reject implausible calorie counts or structurally invalid recipes before persisting
