# Tasks: Database Connection

## Implementation

- [ ] Create `storage/db.py` with `_db` singleton, `init_db()`, `get_db()`, and `close_db()`
- [ ] Export `init_db`, `get_db`, `close_db` from `storage/__init__.py`
- [ ] Wire `init_db` into `bot/main.py` `post_init` hook
- [ ] Wire `close_db` into `bot/main.py` `post_shutdown` hook

## Testing

- [ ] Write a test that calls `init_db()` and asserts `get_db()` returns a connection
- [ ] Write a test that asserts `get_db()` raises `RuntimeError` before `init_db()` is called
- [ ] Write a test that calls `close_db()` and asserts the connection is cleaned up

## Verification

- [ ] Run `uv run pytest` and confirm all tests pass
- [ ] Run the bot locally and confirm the DB file is created at `DATABASE_PATH`
