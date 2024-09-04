import argparse
import asyncio
import json
import os
from pathlib import Path

from openai import AsyncOpenAI
from telegram import ForceReply, Update, ChatFullInfo, UserProfilePhotos
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from core.ai import get_ai_response
from core.task import PromptTask
from core.utils import html_escape

# Fast Demo
demo_task = PromptTask(task_dir='data/dates')
demo_matcher = demo_task.get_matcher()

aclient = AsyncOpenAI(
    api_key=os.environ['DS'],
    base_url='https://api.deepseek.com/beta'
)

async def process_snippet(idd, name, snippet_dct, aclient, prompt, matcher, task):
    snippet_txt = snippet_dct['txt']
    snippet_answer = snippet_dct['answer']
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
        '<code>',
        f'Score: {matcher.score():.2f}%',
        '-' * 10,
    ]
    for idd, name, score, result_data, answer_data in sorted(results):
        lines.append(f'{idd + 1}. {name}: {score:.2f}: {result_data = }, {answer_data = }')
    lines.append('</code>')
    return '\n'.join(lines)

class TGBotHandler:

    def __init__(self, args: argparse.Namespace):
        self.data_root = Path(args.data_root)

    ######################
    #  GENERAL MESSAGES  #
    ######################

    # Define a few command handlers. These usually take the two arguments update and
    # context.
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
            result_msg = await compute_open_task(demo_task, aclient, prompt, demo_matcher)
            await update.effective_user.send_message(result_msg, parse_mode='HTML')
        else:
            for idd, (name, snippet_dct) in enumerate(demo_task.open_snippets.items()):
                await update.effective_user.send_message(f'Processing Task {idd + 1}. {name}')
                snippet_txt = snippet_dct['txt']
                snippet_answer = snippet_dct['answer']
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
                    f'Result data:\n<code>{result_data}</code>\n'
                    f'Answer data:\n<code>{answer_data}</code>\n'
                    f'Result message:\n<code>### BEGIN ###\n{result_msg}\n### END ###</code>\n', parse_mode='HTML'
                )
        context.user_data["prompt"] = ""



