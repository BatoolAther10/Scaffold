from dotenv import load_dotenv
import os
from openai import OpenAI
import memory
import json
from datetime import datetime
import time as what

MAX_ROUNDS = 5
N = 10

load_dotenv()
api_key = os.getenv("NEBIUS_API_KEY")
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=api_key)

tools = [
    {
        "type": "function",
        "function": {
            "name": "save_reminder",
            "description": "Use this when the user asks to be reminded of something at a specific time. If the time is missing, ask for it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_text": {"type": "string", "description": "The text of the reminder."},
                    "due_at": {"type": "string", "description": "The reminder time as local IST time, format YYYY-MM-DDTHH:MM:SS."}
                },
                "required": ["reminder_text", "due_at"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_habit",
            "description": "Log a completed study habit and award XP.",
            "parameters": {
                "type": "object",
                "properties": {"habit_name": {"type": "string", "description": "The name of the task completed."}},
                "required": ["habit_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_status",
            "description": "Get the user's current XP, level, and streak.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def handle_turn(user_id, user_text):
    memory.save_message(user_id, 'user', user_text)
    messages = memory.fetch_messages(user_id, N)
    now = datetime.now()
    weekday = now.strftime("%A")
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    system_prompt = f"""You are a study companion for one student.
Today is {weekday}, {date}. Current time {time}. Timezone IST.

TONE
- Plain, warm, direct. No markdown.
- Keep replies under 120 words.

ANSWERING FROM DOCUMENTS
- Answer only from text returned by the search_documents tool.
- End each factual sentence with the page: (p. N).
- If the tool returns nothing useful, reply exactly: I couldn't find that in your uploaded documents.

TUTORING (hint ladder)
- When asked for help solving something, do not give the answer. Ask one guiding question first.
- Give the full answer only if the student says "just tell me".

GAMIFICATION
- If the student reports completing a study task, praise them and use the log_habit tool.
- Use the get_status tool if they ask about XP, level, or streak.

DEADLINES
- Use save_reminder only when the student gives both a task and a specific time. due_at must be local IST time, format YYYY-MM-DDTHH:MM:SS.

WHEN THE STUDENT IS STRESSED
- You are a study companion, not a therapist. Your goal is to help them self-regulate and connect with humans.
- First: acknowledge the feeling warmly.
- Second: Offer ONE simple self-regulation tip (box breathing or the 2-minute rule).
- Third: Ask one question to help them process it.
- Finally: Gently encourage human connection (e.g., "Have you talked to a friend about this?")."""

    history = [{"role": "system", "content": system_prompt}] + messages
    final_text = "Sorry, something went wrong."
    
    for i in range(MAX_ROUNDS):      
        response = client.chat.completions.create(model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", messages=history, tools=tools)
        message = response.choices[0].message
        
        if not message.tool_calls:
            final_text = (message.content or "").strip()
            break
        else:
            history.append(message)
            for tool_call in message.tool_calls:
                result = "Error: Unknown tool."
                try:
                    keep = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    keep = None
                if keep is None:
                    result = "Error: Invalid JSON."
                elif tool_call.function.name == "save_reminder":
                    result = memory.save_reminder(user_id, keep.get("reminder_text"), keep.get("due_at"))
                elif tool_call.function.name == "log_habit":
                    result = memory.log_habit(user_id, keep.get("habit_name"))
                elif tool_call.function.name == "get_status":
                    result = memory.get_status(user_id)
                history.append({"role": "tool", "content": result, "tool_call_id": tool_call.id, "name": tool_call.function.name})

    memory.save_message(user_id, 'assistant', final_text)
    return final_text
