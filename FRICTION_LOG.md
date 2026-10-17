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