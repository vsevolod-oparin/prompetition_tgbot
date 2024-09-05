import argparse
import asyncio
import os
from pathlib import Path
from typing import List

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.partial import Partial
from bot_partials.state import MessageState
from bot_partials.task_management import TaskManager
from core.ai import get_ai_response
from core.task import PromptTask
from core.utils import html_escape

# Fast Demo
demo_task = PromptTask(task_dir='data/dates_en')
demo_matcher = demo_task.get_matcher()

aclient = AsyncOpenAI(
    api_key=os.environ['DS'],
    base_url='https://api.deepseek.com/beta'
)

async def process_snippet(idd, name, snippet_dct, aclient, prompt, matcher, task):
    snippet_txt = snippet_dct['Task']
    snippet_answer = snippet_dct['Answer']
    result = await get_ai_response(
        client=aclient,
        system_prompt=prompt,
        prompt=snippet_txt
    )
    result_data = task.reply_pipe(result)
    answer_data = task.answer_pipe(snippet_answer)
    score = matcher.accumulate(result_data, answer_data)
    return idd, name, score, result_data, answer_data


async def compute_open_task(task, aclient, prompt, matcher):
    tasks = []
    for idd, (name, snippet_dct) in enumerate(task.open_snippets.items()):
        tasks.append(process_snippet(idd, name, snippet_dct, aclient, prompt, matcher, task))
    results = await asyncio.gather(*tasks)

    lines = [
        f'<b>Score: {matcher.score() * 100:.2f}%</b>',
        '<code>',
    ]
    for idd, name, score, result_data, answer_data in sorted(results):
        lines.append(f'{idd + 1}. {name}\n  score: {score:.2f}\n  {result_data = }\n  {answer_data = }')
    lines.append('</code>')
    return '\n'.join(lines)

class TGBotHandler(Partial):

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.PROMPT_EDIT, MessageState.IDLE]

    ######################
    #  GENERAL MESSAGES  #
    ######################

    # Define a few command handlers. These usually take the two arguments update and
    # context.
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.message.reply_text('Starting very demo bot.')

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



