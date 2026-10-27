from dotenv import load_dotenv
import os
from openai import OpenAI
import memory
import json
from datetime import datetime
import time as what
import crisis
import pathlib
import docs

MAX_ROUNDS=5
N=10

prompts_path = pathlib.Path(__file__).parent / "prompts" / "system_prompt.txt"
PROMPTS_TEMPLATE = prompts_path.read_text(encoding="utf-8")

load_dotenv()
api_key = os.getenv("NEBIUS_API_KEY")
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=api_key
)

tools = [
    {
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
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search the user's own documents (PDFs, notes, syllabus). Use this whenever the user asks about their files, deadlines, rules or anything that may be in their documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Key words from the user's question."
                    }
                },
                "required": ["question"]
            }
        }
    }
]

def run_search_documents(arguments_json):
    try:
        question = json.loads(arguments_json).get("question", "")
    except (json.JSONDecodeError, AttributeError):
        return "Error: invalid arguments."
    results = docs.search_documents(question)
    if not results:
        return ("NOT FOUND: nothing matching in the user's documents. "
                "Say it was not found in the documents. Do not answer from general knowledge.")
    return json.dumps(results)

def handle_turn(user_id, user_text):
    if (crisis.is_crisis(user_text)):
        msg = crisis.CRISIS_REPLY
        memory.save_message(user_id, 'user', user_text)
        memory.save_message(user_id, 'assistant', msg)
        return msg
    memory.save_message(user_id, 'user', user_text)
    messages = memory.fetch_messages(user_id, N)
    now=datetime.now()
    weekday = now.strftime("%A")
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    system_text = PROMPTS_TEMPLATE.replace("{weekday}", weekday).replace("{date}", date).replace("{time}", time)
    history = [{"role": "system", "content": (system_text)}] + messages
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
                elif tool_call.function.name == "search_documents":
                    result = run_search_documents(tool_call.function.arguments)
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

