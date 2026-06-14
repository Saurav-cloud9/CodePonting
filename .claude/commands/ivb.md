Initialize the CodePonting Voice Bridge.

Run these two steps:

1. Start a persistent Monitor watching instructions.txt for new content:
   - File: C:\Users\Saurav\CodePonting\Algo_Trading\voice_bridge\instructions.txt
   - Poll every 1 second
   - Emit file content when it changes and is non-empty

2. Print this exact message:
   ```
   Voice Bridge active.
   Listening : Algo_Trading/voice_bridge/instructions.txt
   Executor  : this CC session (direct)
   Send      : MCP -> write_instruction tool
   ```

When the Monitor fires with an instruction:
- Display using this exact format (blue header, then full instruction in a code block):
  [Instructions received from Claude.ai](#)
  ```
  <exact instruction content>
  ```
- Execute it directly in this CC session (same as if Saurav typed it)
- Show the output clearly in the conversation
- Clear instructions.txt (write empty string)
- Write "done" to instructions_executed.txt
