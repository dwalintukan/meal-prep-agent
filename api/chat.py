from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models import User


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/chat/stream")
async def chat_stream(message: str, user: User = Depends(get_current_user)):
    config = {"configurable": {"thread_id": str(user.id)}}
