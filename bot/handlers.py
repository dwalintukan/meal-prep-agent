from telegram import Update
from telegram.ext import ContextTypes

from agent import route
from agent.workflows import PendingAction


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context._chat_id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Classify and route to proper workflow
    user_message = update.message.text
    print("User:", user_message)

    # Call LLM
    bot_reply, pending_action = await route(
        user_message,
        context.bot_data["anthropic_client"],
        context.bot_data["recipe_store"],
        context.bot_data["weekly_plan_store"],
        context.bot_data["shopping_item_store"],
    )
    print("Bot:", bot_reply)

    # Handle multi-step actions
    _handle_pending_action(pending_action, context)

    for chunk in _split_message(bot_reply, limit=4096):
        await update.message.reply_text(chunk, parse_mode="Markdown")


def _handle_pending_action(
    action: PendingAction | None, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # No pending action, do nothing
    if action is None:
        return

    match action.type:
        case "confirm_recipe":
            context.user_data["pending_action"] = action


def _split_message(text: str, limit: int = 4096) -> list[str]:
    # Message is already under the limit, send it as whole
    if len(text) <= limit:
        return [text]

    chunks, curr_chunk, curr_len = [], [], 0
    for line in text.splitlines():
        line_len = len(line)
        if curr_len + line_len > limit:
            # Putting current line goes over the limit, start new chunk
            chunks.append("\n".join(curr_chunk))
            curr_chunk.clear()
            curr_len = 0

        # Append to chunk and track length
        curr_chunk.append(line)
        curr_len += line_len + 1

    # Append last chunk if not empty
    if curr_len > 0:
        chunks.append("\n".join(curr_chunk))

    return chunks
