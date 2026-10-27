from dotenv import load_dotenv
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
import agent
import memory
import docs

load_dotenv()

token_key = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    try:
        assistant_response = await asyncio.to_thread(
            agent.handle_turn, user_id, user_message
        )
    except Exception as e:
        logging.error(f"handle_turn failed for user {user_id}: {e}")
        assistant_response = "Sorry, something went wrong. Please try again."
    await update.message.reply_text(f"Assistant: {assistant_response}")

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    reminders = memory.due_reminders()
    for reminder_id, user_id, reminder_text in reminders:
        try:
            await context.bot.send_message(chat_id=user_id,
                                           text=f"Reminder: {reminder_text}")
            memory.mark_done(reminder_id)
        except Exception as e:
            logging.error(f"Failed to send reminder to user {user_id}: {e}")

if __name__ == "__main__":
    memory.setup()
    docs.ingest_folder()
    application = ApplicationBuilder().token(token_key).build()
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)
    application.job_queue.run_repeating(check_reminders, interval=60, first=10)
    application.run_polling()