from fastapi import APIRouter, Request

from models import WaitlistSignupCreate
from storage import WaitlistStore

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post("")
async def create(data: WaitlistSignupCreate, request: Request):
    """
    Returns 200 whether the email is new or a duplicate,
    so we don't leak who is already on the list.
    TODO: Currently unauthenticated and subject to bots/malicious actors.
    """
    store: WaitlistStore = request.app.state.waitlist_store
    await store.create(data)
    return {"status": "ok"}
