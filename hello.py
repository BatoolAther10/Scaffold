from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

api_key = os.getenv("NEBIUS_API_KEY")

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=api_key
)

response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[{"role": "user", "content" : "Hello, how are you?"}]
)

print(response.choices[0].message.content)

