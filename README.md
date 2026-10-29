# Personal AI: a private assistant that plans your time and builds your knowledge

A Telegram bot for students. It remembers you, reads documents you permit, answers with citations, saves reminders from plain English, and suggests reading sources. It is built to help you think, not to think for you.

**Track:** Personal AI | **Hackathon:** Nebius x NVIDIA Global AI Hackathon
**Team:** Rafooz (infrastructure, memory, tools, bot) and Batool (prompts, safety wording, test sets, narrative)
**License:** MIT (the demo PDF has its own license, see "Try it")

## What it does

- **Persistent memory:** every conversation is stored per user in a local SQLite database, so the bot remembers across restarts.
- **Cited answers from your documents:** it searches your TXT and PDF files and answers with the file name and page. If the answer isn't in the files, it says "I couldn't find that in your documents" and does not guess.
- **Chat upload:** send a TXT or PDF in the chat. It is stored under your own user ID, and other users cannot search it.
- **Reminders by plain English:** "Remind me to call my friend at 7:30 PM" is saved and delivered by the bot at that time (IST). After a document answer that contains a deadline, the bot offers a reminder and saves it only after a clear "yes".
- **Sources for further reading:** ask for links and it returns up to 3 web results (title and URL) through Tavily. The tool is designed to send only topic words, never your documents.
- **Crisis path:** a plain-code check runs **before** the model. If a message matches a crisis phrase, the bot sends a fixed, warm reply with helplines and the model is never called.

## How the technology is used

| Part | Where it is used |
|---|---|
| **NVIDIA Nemotron** | Model `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` handles all conversation and tool calling (`agent.py`). |
| **Nebius Token Factory** | Every model call goes to the Token Factory inference API (`https://api.tokenfactory.nebius.com/v1/`) through the OpenAI-compatible Chat Completions API. |
| **Tavily** | `sources.py` makes a runtime call to the Tavily Search API for the "find sources" tool. |
| **SQLite (FTS5)** | Memory, reminders and full-text document search (`memory.py`, `docs.py`). |
| **python-telegram-bot** | The Telegram interface and the reminder scheduler (`bot.py`). |

## Architecture

```
Student (Telegram)
      |
   bot.py  --- uploads --> docs.py (ingest to SQLite FTS5, per user)
      |
   agent.py
      |-- crisis.py: crisis check first -> fixed reply (no model call)
      |-- prompt from prompts/system_prompt.txt + last 10 messages
      |-- Nemotron on Nebius Token Factory
      |      |-- tool: search_documents -> docs.py
      |      |-- tool: save_reminder    -> memory.py
      |      |-- tool: find_sources     -> sources.py -> Tavily
      |-- reply saved to memory.py and sent to the student
   bot.py job (every 60 s): sends due reminders
```

The agent loop: if the model asks for a tool, the code runs it, appends the result, and calls the model again until it returns plain text (maximum 5 rounds).

## Setup

You need Python 3 (developed on 3.14), Git, a Nebius Token Factory key, a Telegram bot token from BotFather, and (optional) a Tavily key.

1. `git clone https://github.com/BatoolAther10/personal-ai.git`
2. `cd personal-ai`
3. Create and activate a virtual environment:
   - Windows PowerShell: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in the values:
   - `NEBIUS_API_KEY=`
   - `TELEGRAM_BOT_TOKEN=`
   - `TAVILY_API_KEY=` (without it, the sources feature says it is not set up)
6. Put demo documents (TXT or PDF) in `docs_samples/`.
7. Run `python bot.py` and message your bot on Telegram.

Never commit `.env`, `.venv`, `*.db` or `user_docs/`. They are in `.gitignore`.

## Try it (demo)

- **Demo bot:** https://t.me/originskbot
- **Availability:** the bot runs on a team member's computer in Hyderabad, India (IST, UTC+5:30). Planned online hours on Dec 1 to 15, 2026: 6:00 PM to 12:00 AM IST (about 5:30 AM to 11:30 AM Pacific). Outside these hours the bot may be offline and will not reply; a screen recording of the full flow is in our demo video.
- Suggested test messages:
  1. "hello"
  2. Send a PDF in the chat, then ask a question about it.
  3. Ask something that is not in your files. It should say it could not find it.
  4. "Remind me to submit my report tomorrow at 6 pm"
  5. "Give me sources on spaced repetition"
- The shared demo folder contains the Wikipedia article "Spaced repetition" (Wikipedia contributors, https://en.wikipedia.org/wiki/Spaced_repetition, retrieved 27 Oct 2026), used under the Creative Commons Attribution-ShareAlike 4.0 License, plus two small sample files. This PDF is not covered by the MIT license of the code.

## Privacy

- Messages and reminders are stored in `agent.db` on the machine running the bot. Uploaded files are stored in `user_docs/<your user ID>/`. Nothing is encrypted, and the people running the bot can technically read stored data. Please do not send sensitive personal information to the demo.
- Each user can search only their own uploads plus the shared demo files. The user ID comes from Telegram and is supplied by code, never by the model.
- Your messages are sent to the Nebius Token Factory model endpoint to produce replies. The shared endpoint's region can change, so do not send anything you would not want processed there.
- The sources tool is told to send Tavily only topic words. The model chooses the query, and our code does not filter it, so avoid putting personal details in a sources request.
- Documents are read only from the demo folder and from files you send yourself.

## Safety

- This is a **self-reflection and learning tool. It is not therapy, medical advice or treatment.**
- The crisis check runs in plain code before the model, with a phrase list that includes indirect phrasing. The reply is fixed text and encourages contact with a real person. The helplines are India-specific and were checked by the team on their official sites on [DATE YOU CHECKED]: https://telemanas.mohfw.gov.in/home, https://www.vandrevalafoundation.com/free-counseling, https://www.aasra.info/helpline.html, https://1life.org.in/, https://www.jeevanaastha.com/
- The model is told to answer document questions only from search results, to cite every claim, and to say so when it cannot find something.
- We do not claim zero hallucination. We aim for verifiability: citations, a "not found" behaviour, and measured accuracy on small test sets (below).

## Testing (internal, small sets)

| Test | Result |
|---|---|
| Crisis phrases (20 phrasings) | 20 of 20 caught. The phrase list was expanded while testing, so this is a sanity check, not an independent score |
| Ordinary and stress messages (35 lines) | 0 falsely flagged |
| Document questions, first run (10 answerable, 3 not in the file) | 8/10 correct citations, 3/3 "not found". All answers were right; 2 cited a reference page, which we fixed |
| Same 13 questions after the fix | 13/13 (this set was used to tune the bot) |
| New untuned set, one run | 7/7 |

These are small tests run by the team, not a formal evaluation.

## Limitations

- Search is keyword-based, so exact wording matters ("quiz 1" works; "quiz1" may not).
- Only TXT and PDF are supported, up to 10 MB per upload. Scanned PDFs, images and text inside graphs are not read.
- For TXT files, "page" means line number.
- Replies can take from a few seconds to 30 to 40 seconds because of model latency.
- Reminders run inside the bot process, so they are delivered only while the bot is running. Reminders that fell due while it was off are delivered on restart.
- The bot runs on one machine, so it is offline when that machine is off.
- No per-user rate limit is built yet, so heavy use spends the team's credits.
- Crisis detection is phrase-based and can both miss unusual wording and flag a false alarm. It is a safety net, not a diagnosis.
- The helplines are for India only.

## What we built during the submission period

The whole project was built during the submission period (from 16 Oct 2026): memory, the Telegram bot, the tool-calling loop, reminders, the crisis path, document search with citations, chat upload, and the Tavily sources tool.

## Future work

- Plan mode: tasks and deadlines from files into a daily plan.
- Independence trend: tracking how often the student attempts before taking a hint.
- Habits and XP (Batool's design), with a daily XP cap and tool-failure handling.
- A hosted deployment with persistent storage, and OCR for scanned documents.
- A Brev + NemoClaw/Hermes deployment plan (Batool's design).

## Acknowledgements

Built with NVIDIA Nemotron, Nebius Token Factory, Tavily, SQLite, python-telegram-bot and pypdf.