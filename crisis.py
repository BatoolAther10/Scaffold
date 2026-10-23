import pathlib

CRISIS_PHRASES_PATH = pathlib.Path(__file__).parent / "crisis_phrases.txt"
phrase_text = CRISIS_PHRASES_PATH.read_text(encoding="utf-8")
CRISIS_PHRASES = [
    " ".join(line.strip().replace("’", "'").split())
    for line in phrase_text.splitlines()
    if line.strip()
]

FALLBACK_REPLY = " I’m really sorry you’re feeling this way, and I’m glad you told me. " \
"You don’t have to carry this alone. Please reach out to someone you trust right now, " \
"like a friend, a family member, or someone near you." \
"If you are in immediate danger, call 112 (India)." \
"You can also call Tele-MANAS: 14416 or 1800-89-14416. " \
"You matter, and people want to help you."
CRISIS_TEXT = pathlib.Path(__file__).parent / "crisis.txt"
try:
    crisis_reply = CRISIS_TEXT.read_text(encoding="utf-8").strip()
except FileNotFoundError:
    print(f"Warning: {CRISIS_TEXT} was not found; using fallback reply.")
    CRISIS_REPLY = FALLBACK_REPLY
else:
    if crisis_reply:
        CRISIS_REPLY = crisis_reply
    else:
        print(f"Warning: {CRISIS_TEXT} is empty; using fallback reply.")
        CRISIS_REPLY = FALLBACK_REPLY



def is_crisis(text):
    text_lower = " ".join(text.lower().replace("’", "'").split())
    for phrase in CRISIS_PHRASES:
        if phrase.lower() in text_lower:
            return True
    return False
