# Meal Prep Agent

An AI Agent helping you solve one of the hardest questions out there: "What to eat for dinner?"

Uses a Telegram Bot to interact with the agent.

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

## Architecture

A Telegram bot that uses Claude AI for meal planning. Messages are intent-classified, then routed to a workflow that calls Claude to select recipes or parse new ones.

```plaintext
Telegram Message
      ↓
Intent Classifier (claude-haiku-4-5, forced tool schema)
      ├→ "plan"       → MealPlanWorkflow (claude-sonnet-4-6)
      ├→ "add_recipe" → AddRecipeWorkflow (claude-sonnet-4-6)
      └→ "chat"       → ChatWorkflow (claude-sonnet-4-6 + history)
```

## Environment

Create an `.env` file at root and fill in:
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_PATH` (default: `data/meal_prep.db`)
