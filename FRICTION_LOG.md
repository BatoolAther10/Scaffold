## Day-1 (Fri 16 Oct 2026)

### Tool Friction
* The key was shown only once at creation so had to copy it.
* I received a 401 error when I tried running the hello.py file because it has rejected my key, so I went to token factory, deleted the old api key and created a new one and updated the new key and tried again. 
These actions have helped me resolve the issue and get a response from the model.

## Day-2 (Sat 17 Oct 2026)

### My mistakes
* The problems faced were mostly variable naming mistakes like having quotes around text which made them to be considered as a string, which created a new database called db_name.
* Next using history.reverse() in fetch_messages() function in memory.py which printed None, so changed it to list(reversed(history)) which gives all messages with the oldest message first.
* In agent.py for role made a simple typo mistake of "System" for "system".
### Tool Friction
Faced no problems today, the model worked as intended.

## Day-3 (Sun 18 Oct 2026)

### My mistakes
* Telegram bot timed out at start (telegram.error.TimedOut when run_polling started) and after trying again by changing the internet connection, it started working (cause unverified, most probably network).
### Tool Friction
* The nemotron model replies in markdown format by default(**Rafooz**), but my bot replies in plain text.

## Day-4 (Mon 19 Oct 2026 & Tue 20 Oct 2026)

### Tool Friction
* Latency from about 2s to 30s for similar requests, with token counts.
* A reminder costs about 8s for two rounds.
* Reasoning tokens inflate completion_tokens, and the API doesn’t show the split.
* The docs example uses a different model and stops before the second call.

## Day-5 (Wed 21 Oct 2026)

### Tool friction
* Response time varied a lot with no code change. A reply with no tool call took 18.56s in one run and 2.56s in another. Tool-call turns took two model rounds, for example 5.08s + 2.87s and 5.41s + 2.20s, so a reminder takes about 8 to 10s end to end. Cause unverified. A note in the docs on expected latency for Nemotron-3-Nano would help.
* The model sometimes handles a past time itself (it asked us for a new time without calling the tool) and sometimes calls the tool and relays our error. This makes the code-side check hard to test through the model, so we test the function directly.
* When asking for a new time, the model gave an example date in the past ("2025-04-05"). It does not seem to anchor examples to the date in the system message.

### Other tools
* python-telegram-bot: JobQueue needs an extra install (`pip install "python-telegram-bot[job-queue]"`). The plain install does not mention this.
* python-telegram-bot docs: datetimes without a timezone are treated as UTC by default. Easy to miss when stored times are in IST.
* SQLite Viewer (VS Code extension): deleting rows asks for a premium upgrade. So deleted test rows with Python's sqlite3 instead.

## Day-6 (Thu 22 Oct 2026 and Fri 23 OCt 2026)

### Tool Friction
* Model output sometimes has joined words ("justa bit", "canmake", "stretchbreak", "time(in IST)"). Seen once in a terminal test. Cause unverified (model or endpoint).
* Even with a plain system prompt, replies use Markdown, bold, lists and emojis. The same chat on Telegram shows literal asterisks. Needs an explicit "no markdown" instruction.
* Model latency again varied from about 2s to 4s for short replies with no code change.
* After a fixed crisis reply, the model answered "ok thanks" cheerfully. History alone does not set tone.

## Day-7 (Fri 23 Oct 2026)

### Tool Friction
* Reply time for the same kind of message ranged from 1.5s to 12s, with no code change. The reminder took 12s, then 2.9s, for two model rounds.
* The model said a reminder was "set for 22:42:42", but the model's words are not proof. I had to check the database row myself.