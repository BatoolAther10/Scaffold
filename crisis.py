import pathlib

CRISIS_PHRASES_PATH = pathlib.Path(__file__).parent / "crisis_phrases.txt"
phrase_text = CRISIS_PHRASES_PATH.read_text(encoding="utf-8")
CRISIS_PHRASES = [line.strip() for line in phrase_text.splitlines() if line.strip()]

CRISIS_TEXT = pathlib.Path(__file__).parent / "crisis.txt"
CRISIS_REPLY = CRISIS_TEXT.read_text(encoding="utf-8")


def is_crisis(text):
    text_lower = text.lower()
    for phrase in CRISIS_PHRASES:
        if phrase.lower() in text_lower:
            return True
    return False
