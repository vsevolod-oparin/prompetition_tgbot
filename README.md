# Prompetition Bot

The Telegram bot to run competition for the seek of the best prompts.

The bot: https://t.me/prompetition_bot

## Rules

Each task consists of two parts -- open and hidden. Open part is to test the prompt and see explicitly how LLM proceeds.

The hidden part is to score that will appear in leaderboard. It's quite obvious that one can just hardcode all outputs right into prompt. So I hide the snippets there.

## General way of usage

- Start bot
- Enter your name
- See the tasks by /task_list
- Select the task with /task_select. E.g. `/task_select dates_en`.
- Enter the prompt.
- /run_open to see how it works on the open part.
- /run_to_score to get the score on the hidden part.

## Installation and run

Go to TG:BotFather and DeepSeek to obtain the API keys. 

```commandline 
pip3 install -r requirements.txt
export TG_TOKEN=<Telegram Bot API>
export DS=<DeepSeek API>
python3 bot.py
```

### Custom LLMs

If you want to use another OpenAPI LLM just add it into `data/llm_config` and mention its usage under `llm` in `task / info.json`.

## Bot commands

TG Commands Control

```
start - start the bot
help - help command
whoami - get name
set_name - set new name
switch_debug_mode - to switch debug mode
switch_autoclean - empty prompt after submit
prompt_fetch - fetch current prompt
task_show - show current task
task_list - list the tasks
task_select - list the tasks
snippet_list - list snippets per task
snippet_focus - select to snippet to run prompt on
snippet_unfocus - forget snippet selection
run_snippet - run prompt only on snippet under focus
run_open - run prompt on open part
run_to_score - run prompt on hidden part to get score
leaderboard - leaderboard per task
```

### Future plans

**Future developments**

Functionality:
- Add needed parameters to control (temperature, freq penalty and so on)
- Add honoring medals

Interface
- Implement callbacks to update status.
- Add menu buttons
- Rename switch debug to something like hide details

Back infra
- Add task verification
