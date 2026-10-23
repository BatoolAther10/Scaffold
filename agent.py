from dotenv import load_dotenv
import os
from openai import OpenAI
import memory
import json
from datetime import datetime
import time as what
import crisis

MAX_ROUNDS=5
N=10

load_dotenv()
api_key = os.getenv("NEBIUS_API_KEY")
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=api_key
)

tools = [{
    "type": "function",
    "function": {
        "name": "save_reminder",
        "description": "Use this when the user asks to be reminded of something at a specific time. If the time is missing or vague, such as 'remind me on Monday', ask the user for the time instead of guessing.",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder_text": {
                    "type": "string",
                    "description": "The text of the reminder."
                },
                "due_at": {
                    "type": "string",
                    "description": "The reminder time as local IST time, with no offset and no Z, exactly in the format YYYY-MM-DDTHH:MM:SS."
                }
            },
            "required": ["reminder_text", "due_at"]
        }
    }
}]
def handle_turn(user_id, user_text):
    if (crisis.is_crisis(user_text)):
        msg = "Please note that I am only a virtual assistant. If you are " \
        "in crisis or need help, please reach out to people around you or contact 14416 or 1800-891-4416 for professional support."
        return msg
    memory.save_message(user_id, 'user', user_text)
    messages = memory.fetch_messages(user_id, N)
    now=datetime.now()
    weekday = now.strftime("%A")
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    history = [{"role": "system", "content": (
    f"You are a helpful assistant. Today is {weekday}, {date}. "
    f"The current time is {time}. The timezone is IST. "
    "Reply to the user in normal, friendly sentences. "
    "Monday means the next upcoming Monday, counted from today. "
    "If the user asks for a reminder but gives no time, ask for the time instead of guessing. "
    "When you call the save_reminder tool, due_at must be local IST time in the exact "
    "format YYYY-MM-DDTHH:MM:SS, with no offset and no Z.")}] + messages
    final_text = "Sorry, something went wrong."
    for i in range(MAX_ROUNDS):      
        start_time = what.perf_counter()
        response = client.chat.completions.create(
            model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
            messages=history,
            tools=tools
        )
        message = response.choices[0].message
        end_time = what.perf_counter()
        print(f"Time taken for model response: {end_time - start_time:.2f} seconds")
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
                    result = "Error: Invalid JSON in tool call."
                elif tool_call.function.name == "save_reminder":
                    result = memory.save_reminder(user_id, keep.get("reminder_text"), keep.get("due_at"))
                history.append({"role": "tool", "content": result,
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name})

    memory.save_message(user_id, 'assistant', final_text)
    return final_text

if __name__ == "__main__":
    memory.setup()
    user_id = int(input("Enter user ID: "))
    while True:
        user_text = input("Enter your message: ")
        if user_text.lower() == "quit":
            break
        assistant_response = handle_turn(user_id, user_text)
        print(f"Assistant: {assistant_response}")

