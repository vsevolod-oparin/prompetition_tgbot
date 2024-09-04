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
switch - to switch debug mode
show_task - show current task
submit - submit prompt
task_list - list the tasks
```

### Implementation plan

**Done**
1. Implement first competition
   1. Collect snippets with texts
   2. Define the task
   3. Find the format of the prompt that achieves something reasonable

**TBD**

2. Define the scheme of data storage
   1. **[Done]** Separate open snippets from hidden
   2. Add needed parameters to control

3. Implement matching scheme

4. Implement leaderboard

5. Integrate everything in Telegram bot