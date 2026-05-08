import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from telegram.ext import Application

from storage import init_db, close_db


async def post_init(application: Application) -> None:
    application.bot_data["db"] = await init_db(
        os.getenv("DATABASE_PATH", "data/meal_prep.db")
    )
    application.bot_data["anthropic_client"] = AsyncAnthropic()
    print("Bot is ready for your command 🤖")


async def post_shutdown(application: Application) -> None:
    db = application.bot_data["db"]
    await close_db(db)


def run() -> None:
    print("Loading env...")
    load_dotenv()

    print("Connecting Telegram bot...")
    app = (
        Application.builder()
        .token(os.environ["TELEGRAM_BOT_TOKEN"])
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.run_polling()
