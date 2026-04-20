# Tests: Database Connection

## Happy Path

- `init_db()` with a valid path creates the DB file and returns without error
- `get_db()` after `init_db()` returns an `aiosqlite.Connection` instance
- `get_db()` called multiple times returns the same connection object
- `close_db()` after `init_db()` closes the connection without error
- `init_db()` creates parent directories if they don't exist (e.g. `data/nested/test.db`)

## Edge Cases

- `get_db()` before `init_db()` raises `RuntimeError`
- `close_db()` before `init_db()` completes without error (no-op)
- `init_db()` called twice does not open a second connection or raise an error
