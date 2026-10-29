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
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


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
    await update.message.reply_text(assistant_response)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    name = os.path.basename(doc.file_name or "")
    if not name.lower().endswith(('.txt', '.pdf')):
        await update.message.reply_text("Please send a .txt or .pdf file.")
        return
    if doc.file_size and doc.file_size > MAX_UPLOAD_BYTES:
        await update.message.reply_text("That file is too big (max 10 MB).")
        return
    folder = os.path.join(docs.USER_FOLDER, str(user_id))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(path)
        count = await asyncio.to_thread(docs.ingest_path, path, user_id)
    except Exception as e:
        logging.error(f"Upload failed for user {user_id}: {e}")
        if os.path.exists(path):
            os.remove(path)
        await update.message.reply_text("Sorry, I couldn't read that file.")
        return
    if count == 0:
        os.remove(path)
        await update.message.reply_text(
            "I found no readable text in that file (a scanned PDF?).")
        return
    await update.message.reply_text(f"Added {name}. You can ask about it now.")


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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(
        MessageHandler(filters.Document.ALL, handle_document))
    application.job_queue.run_repeating(check_reminders, interval=60, first=10)
    application.run_polling()