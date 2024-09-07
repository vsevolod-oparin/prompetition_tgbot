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
switch - to switch debug mode
submit - submit prompt
task_show - show current task
task_list - list the tasks
task_select - list the tasks
snippet_list - list snippets per task
snippet_focus - select to snippet to run prompt on
snippet_unfocus - forget snippet selection
```

## Implementation plan

MVP is ready.

### Future plans

**Before announcements**
+ Implement callbacks to update status.

- Save prompts in DB.
- Add an option to run prompts either on particular snippets, or only open snippets.

- Add logging.
- Fully implement tasks with open and hidden parts

- Add name demand.
- Implement leaderboard

- Rewrite help and greeting message.


**Future developments**
- Add needed parameters to control (temperature, freq penalty and so on)
- Add task verification
- Add medals