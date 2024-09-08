from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.focus import FocusManagement
from bot_partials.partial import Partial
from bot_partials.state import MessageState
from bot_partials.userdata_keys import PROMPT_KEY, AUTOCLEAN_KEY, DEBUG_KEY, STOP_KEY
from core.prompter import PromptRunner
from core.task_management import TaskManager
from core.utils import html_escape, tg_user_id


class TGPrompter(Partial):

    def __init__(self,
                 task_manager: TaskManager,
                 runner: PromptRunner):
        self.task_manager = task_manager
        self.runner = runner

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.PROMPT_EDIT, MessageState.IDLE]

    async def switch_debug_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        debug = context.user_data.get(DEBUG_KEY, False)
        debug = not debug
        context.user_data[DEBUG_KEY] = debug
        message = "Debug mode is on." if debug else "Debug mode is off."
        await update.effective_chat.send_message(message)

    async def switch_autoclean(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        autoclean = context.user_data.get(AUTOCLEAN_KEY, False)
        autoclean = not autoclean
        context.user_data[AUTOCLEAN_KEY] = autoclean
        message = "Autoclean mode is on." if autoclean else "Autoclean mode is off."
        await update.effective_chat.send_message(message)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        prompt = update.message.text
        context.user_data[PROMPT_KEY] = prompt
        prompt = html_escape(prompt)
        prompt.replace('<', '&lt;')
        hints = [
            "Use /run_open, to run the prompt on open part.",
            "Use run /run_to_score, to run the prompt on hidden scorable part.",
            "Use /snippet_focus and /run_snippet, to run on a single snippet.",
        ]
        hint_msg = '\n'.join(hints)
        await update.effective_chat.send_message(
            f"New prompt:\n<code>{prompt}</code>\n\n{hint_msg}", parse_mode='HTML'
        )

    async def run_to_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        # Fast Demo
        focus = FocusManagement(context)
        if focus.task is None:
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            await update.effective_chat.send_message("Please enter your prompt first.")
            return

        message = await update.effective_chat.send_message('Computing...')
        user_id = tg_user_id(update.effective_user.id)
        result_batch = await self.runner.compute_hidden_batch(task, user_id, prompt)
        await message.edit_text(result_batch.tg_html_form_semihidden(), parse_mode='HTML')

        if context.user_data.get(AUTOCLEAN_KEY, False):
            context.user_data[PROMPT_KEY] = ""

    async def run_open(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        # Fast Demo
        focus = FocusManagement(context)
        if focus.task is None:
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            await update.effective_chat.send_message("Please enter your prompt first.")
            return
        context.user_data[STOP_KEY] = False
        debug = context.user_data.get(DEBUG_KEY, False)
        if not debug:
            message = await update.effective_chat.send_message('Computing...')
            user_id = tg_user_id(update.effective_user.id)
            result_batch = await self.runner.compute_open_batch(task, user_id, prompt)
            await message.edit_text(result_batch.tg_html_form(), parse_mode='HTML')
        else:
            matcher = task.get_matcher()
            total = len(task.open_snippets)
            await update.effective_chat.send_message(f"Computing on {total} snippets...")
            for idd, snippet_id in enumerate(task.open_snippets):
                # TODO: potentialy, we can run it in parallel
                if context.user_data.get(STOP_KEY, False):
                    context.user_data[STOP_KEY] = False
                    break
                eval = await self.runner.process_snippet(
                    task=task,
                    snippet_id=snippet_id,
                    prompt=prompt,
                    matcher=matcher,
                )
                prefix = f'{idd + 1}/{total}. '
                await update.effective_chat.send_message(prefix + eval.tg_html_form(), parse_mode='HTML')
            await update.effective_chat.send_message(
                f'Total open avg score: {matcher.score() * 100:.2f}',
                parse_mode='HTML'
            )
        if context.user_data.get(AUTOCLEAN_KEY, False):
            context.user_data[PROMPT_KEY] = ""

    async def run_snippet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        focus = FocusManagement(context)
        if focus.task is None:
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        if focus.snippet is None:
            await update.effective_chat.send_message("No snippet selected. Use /snippet_focus to choose one.")
            return

        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            await update.effective_chat.send_message("Please enter your prompt first.")
            return

        snippet_dct = task.open_snippets.get(focus.snippet, None)
        if snippet_dct is None:
            await update.effective_chat.send_message("Snippet name seems to be broken. Try another one.")
            return

        await update.effective_chat.send_message(f'Processing Task {focus.task} / Snippet: {focus.snippet}')

        matcher = task.get_matcher()
        eval = await self.runner.process_snippet(
            task=task,
            snippet_id=focus.snippet,
            prompt=prompt,
            matcher=matcher,
        )
        await update.effective_chat.send_message(eval.tg_html_form(), parse_mode='HTML')