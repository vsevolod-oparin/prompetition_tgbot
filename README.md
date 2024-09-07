# Prompetition Bot

The Telegram bot to run competition for the seek of the best prompts. 

### Bot commands

Fixed task
- show open snippets
- run prompt on full task -- score only
- run prompt on full task -- debug mode

Extended multi task:
- select task
- list tasks

- run prompt on specific snippet in debug mode

TG Commands Control

```
start - start the bot
help - help command
switch_debug_mode - to switch debug mode
switch_autoclean - empty prompt after submit
task_show - show current task
task_list - list the tasks
task_select - list the tasks
snippet_list - list snippets per task
snippet_focus - select to snippet to run prompt on
snippet_unfocus - forget snippet selection
run_snippet - run prompt only on snippet under focus
run_open - run prompt on open part
run_to_score - run prompt on hidden part to get score
```

## Implementation plan

MVP is ready.

### Future plans

**Before announcements**
- Implement callbacks to update status.

- Save prompts in DB.

- Add logging.
- Fully implement tasks with open and hidden parts

- Add name demand.
- Implement leaderboard

- Rewrite help and greeting message.


**Future developments**
- Add needed parameters to control (temperature, freq penalty and so on)
- Add task verification
- Add medals