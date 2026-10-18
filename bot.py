from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

load_dotenv()

token_key = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message=update.message.text
    await update.message.reply_text(f"You said: {user_message}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(token_key).build()
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)
    application.run_polling()
    