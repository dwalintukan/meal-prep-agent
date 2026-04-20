# Design: Database Connection

## Architecture

- A module-level singleton connection held in `storage/db.py`. A singleton avoids passing a connection object through every constructor and function signature.
- The connection is initialized once at app startup and imported directly by any module that needs it.
- `aiosqlite` serializes all SQLite operations through a single background thread internally — sharing one connection across coroutines is safe and correct.
- A `get_db()` guard (instead of raw global access) makes uninitialized use a loud error rather than a silent `AttributeError`.

## Implementation

**`storage/db.py`**

```python
import aiosqlite

_db: aiosqlite.Connection | None = None

# Inits the singleton DB connection. Ensures it only initializes once.
async def init_db(path: str) -> None:
# Used by all other classes to fetch the DB connection
def get_db() -> aiosqlite.Connection:
# Closes the DB connection if it's been initialized
async def close_db() -> None:
```

Any module imports the connection via:

```python
from storage.db import get_db
```

## Startup / Shutdown

`init_db()` is called once in `bot/main.py`'s `post_init` hook (before polling begins), and `close_db()` is called in `post_shutdown`. This guarantees a single connection for the app's lifetime.

```python
async def post_init(application):
    await init_db(os.getenv("DATABASE_PATH", "data/meal_prep.db"))

async def post_shutdown(application):
    await close_db()
```

## Out of Scope

- Database schemas (separate spec)
- ORM integration
