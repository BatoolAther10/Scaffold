from dotenv import load_dotenv
import os
from openai import OpenAI
import memory
N=10

load_dotenv()
api_key = os.getenv("NEBIUS_API_KEY")
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=api_key
)

def handle_turn(user_id, user_text):
    memory.save_message(user_id, 'user', user_text)
    messages = memory.fetch_messages(user_id, N)
    history = [{"role": "system", "content": "You are a helpful assistant."}] + messages
    response = client.chat.completions.create(
        model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        messages=history
    )
    assistant_text = response.choices[0].message.content.strip()
    memory.save_message(user_id, 'assistant', assistant_text)
    return assistant_text

if __name__ == "__main__":
    memory.setup()
    user_id = int(input("Enter user ID: "))
    while True:
        user_text = input("Enter your message: ")
        if user_text.lower() == "quit":
            break
        assistant_response = handle_turn(user_id, user_text)
        print(f"Assistant: {assistant_response}")

