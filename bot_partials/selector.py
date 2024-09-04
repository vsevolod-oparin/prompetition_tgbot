import argparse
import asyncio
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import List

from openai import AsyncOpenAI
from telegram import ForceReply, Update, ChatFullInfo, UserProfilePhotos
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot_partials.partial import Partial
from bot_partials.state import MessageState
from core.ai import get_ai_response
from core.task import PromptTask
from core.utils import html_escape, from_json_file


class TGSelector(Partial):

    def __init__(self, args: argparse.Namespace):
        self.data_root = Path(args.data_root)
        self.task_conf_list = [
            task_dir / 'info.json'
            for task_dir in self.data_root.glob('*')
            if (task_dir / 'info.json').exists()
        ]

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.TASK_SELECTION]

    def get_task_id_map(self):
        task_conf_list = [
            task_dir / 'info.json'
            for task_dir in self.data_root.glob('*')
            if (task_dir / 'info.json').exists()
        ]
        task_map = dict()
        for task_pth in task_conf_list:
            task_obj = from_json_file(task_pth)
            task_map[task_obj['id']] = task_pth
        return task_map

    def get_current_task(self, task_id: str) -> PromptTask:
        task_pth = self.get_task_id_map()[task_id]
        return PromptTask(Path(task_pth).parent)


    async def task_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        task_conf_list = [
            task_dir / 'info.json'
            for task_dir in self.data_root.glob('*')
            if (task_dir / 'info.json').exists()
        ]
        result_dct = defaultdict(list)
        for task_pth in task_conf_list:
            task_obj = from_json_file(task_pth)
            lang = task_obj['lang']
            result_dct[lang].append(f'- {task_obj["title"]} ({task_obj["id"]})')

        result_lst = []
        for lang, lst in result_dct.items():
            result_lst.append(f'<b>{lang.upper()}</b>')
            result_lst.append('\n'.join(lst))
            result_lst.append('')

        await update.message.reply_text('\n'.join(result_lst).strip(), parse_mode='HTML')

    async def _select_task(self, search_token: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        choices = []
        for idd, pth in self.get_task_id_map().items():
            if search_token in idd:
                choices.append(idd)
        choice_num = len(choices)
        if choice_num == 0:
            await update.effective_user.send_message(f'No task found with id {search_token}.')
            context.user_data['state'] = MessageState.TASK_SELECTION
        elif choice_num == 1:
            context.user_data['task'] = choices[0]
            context.user_data['state'] = MessageState.IDLE
            await update.effective_user.send_message(f'Task `{choices[0]}` has been selected.')
        else:
            multi_choice = "\n- ".join(choices)
            current_task = context.user_data['task']
            suffix = "No task selected." if current_task is None else f"Current task stays: {current_task}"
            await update.effective_user.send_message(
                ' '.join([
                    f'Multiple tasks found:\n- {multi_choice}.',
                    suffix
                ])
            )
            context.user_data['state'] = MessageState.TASK_SELECTION

    async def select_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_token = update.message.text.strip()
        search_token = ' '.join(search_token.split(' ')[1:])
        if search_token == "":
            await update.message.reply_text('Select the task by typing id')
            context.user_data['state'] = MessageState.TASK_SELECTION
        else:
            await self._select_task(search_token, update, context)

    async def show_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        task_id = context.user_data.get('task', None)
        if task_id is None:
            await update.effective_user.send_message("Select the task first. Use /select command.")
            return
        current_task = self.get_current_task(task_id)
        await update.effective_user.send_message(current_task.short_description(), parse_mode='HTML')

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data['state'] == MessageState.TASK_SELECTION:
            search_token = update.message.text.strip()
            await self._select_task(search_token, update, context)
        else:
            context.user_data['state'] = MessageState.IDLE

    ######################
    #  GENERAL MESSAGES  #
    ######################

    # Define a few command handlers. These usually take the two arguments update and
    # context.

    '''
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.message.reply_text('Starting very demo bot.')

    async def show_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.effective_user.send_message(str(demo_task), parse_mode='HTML')

    async def switch_debug_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        debug = context.user_data.get("debug", False)
        debug = not debug
        context.user_data['debug'] = debug
        message = "Debug mode is on." if debug else "Debug mode is off."
        await update.effective_user.send_message(message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("Help!")

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        prompt = update.message.text
        context.user_data["prompt"] = prompt
        prompt = html_escape(prompt)
        prompt.replace('<', '&lt;')
        await update.effective_user.send_message(
            f"New prompt:\n<code>{prompt}</code>\n\nDon't forget to run /submit.", parse_mode='HTML'
        )

    async def submit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        prompt = context.user_data.get("prompt", "")
        if prompt == "":
            await update.effective_user.send_message("Please enter your prompt first.")
            return
        debug = context.user_data.get("debug", False)
        if not debug:
            message = await update.effective_user.send_message('Computing...')
            result_msg = await compute_open_task(demo_task, aclient, prompt, demo_matcher)
            await message.edit_text(result_msg, parse_mode='HTML')
            # await update.effective_user.send_message()
        else:
            for idd, (name, snippet_dct) in enumerate(demo_task.open_snippets.items()):
                await update.effective_user.send_message(f'Processing Task {idd + 1}. {name}')
                snippet_txt = snippet_dct['Task']
                snippet_answer = snippet_dct['Answer']
                result_msg = await get_ai_response(
                    client=aclient,
                    system_prompt=prompt,
                    prompt=snippet_txt
                )
                result_data = demo_task.reply_pipe(result_msg)
                answer_data = demo_task.answer_pipe(snippet_answer)
                score = demo_matcher.accumulate(result_data, answer_data)
                await update.effective_user.send_message(
                    f'Score: <b>{score}</b>\n\n'
                    f'Text:\n<code>{html_escape(snippet_txt)}</code>\n\n'
                    f'Result:\n<code>{result_data}</code>\n'
                    f'Answer:\n<code>{answer_data}</code>\n'
                    f'Result message:\n<code>### BEGIN ###\n{result_msg}\n### END ###</code>\n', parse_mode='HTML'
                )
        context.user_data["prompt"] = ""
        '''



