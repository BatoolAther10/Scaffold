from dotenv import load_dotenv
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import agent
import memory

load_dotenv()
token_key = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['I need help studying', 'I feel stressed'],
        ['My reminders', 'About this bot']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Hi! I'm your study companion. How can I help you today?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # CRISIS CHECK
    crisis_keywords = ["suicide", "kill myself", "want to die", "self-harm", "end it all", "don't want to be here"]
    if any(keyword in user_message.lower() for keyword in crisis_keywords):
        crisis_msg = (
            "If you are in immediate danger, please call emergency services (112 in India).\n\n"
            "You are not alone. Here are verified 24/7 helplines in India:\n\n"
            "- Tele MANAS (Govt of India): 14416\n"
            "- Vandrevala Foundation: +91 9999 666 555\n"
            "- Aasra: 91-9820466726\n"
            "- 1 Life: 78930-78930\n"
            "- Jeevan Aastha: 1800 233 3330\n\n"
            "Please reach out to one of these numbers. They are there to help you."
        )
        await update.message.reply_text(crisis_msg)
        return 

    assistant_response = agent.handle_turn(user_id, user_message)
    await update.message.reply_text(assistant_response)

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    reminders = memory.due_reminders()
    for reminder_id, user_id, reminder_text in reminders:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"Reminder: {reminder_text}")
            memory.mark_done(reminder_id)
        except Exception as e:
            print(f"Failed to send reminder: {e}")

if __name__ == "__main__":
    memory.setup()
    application = ApplicationBuilder().token(token_key).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.job_queue.run_repeating(check_reminders, interval=60, first=10)
    
    application.run_polling()
