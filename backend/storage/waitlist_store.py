from uuid import UUID
import asyncpg
import structlog

from models import WaitlistSignupCreate

log = structlog.get_logger()


class WaitlistStore:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create(self, data: WaitlistSignupCreate) -> UUID | None:
        """
        Insert a signup. Returns the new id, or None if the email was
        already on the list (idempotent — a repeat submit is not an error).
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                id = await conn.fetchval(
                    "INSERT INTO waitlist_signups (email, source) "
                    "VALUES ($1, $2) ON CONFLICT (email) DO NOTHING RETURNING id",
                    data.email,
                    data.source,
                )
                if id is None:
                    log.info("waitlist_signup_duplicate", email=data.email)
                else:
                    log.info("waitlist_signup_created", id=id, email=data.email)
                return id
