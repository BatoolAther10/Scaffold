import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")

MAX_RESULTS = 3


def find_sources(topic):
    if not isinstance(topic, str) or not topic.strip():
        return "Error: topic must be a non-empty string."
    if not api_key:
        print("Tavily error: API key not configured")
        return "Error: source search is not set up."

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=topic.strip(), max_results=MAX_RESULTS)
    except Exception as e:
        print(f"Tavily error: {type(e).__name__}")
        return "Error: source search is not available right now."

    if not isinstance(response, dict):
        return "Error: source search returned something unexpected."

    lines = []
    for item in response.get("results", [])[:MAX_RESULTS]:
        url = item.get("url")
        if not url:
            continue
        title = item.get("title") or "Untitled"
        snippet = (item.get("content") or "")[:200]
        lines.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")

    if not lines:
        return "NOT FOUND: no sources found for that topic."
    return "\n\n".join(lines)


if __name__ == "__main__":
    print(find_sources("spaced repetition"))