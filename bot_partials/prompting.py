from logging import Logger
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.focus import FocusManagement
from bot_partials.partial import Partial
from bot_partials.state import MessageState
from bot_partials.userdata_keys import PROMPT_KEY, AUTOCLEAN_KEY, DEBUG_KEY, STOP_KEY
from core.llm_manager import LLMManager
from core.prompter import PromptRunner
from core.task_management import TaskManager
from core.utils import html_escape, tg_user_id

DEFAULT_DEBUG_STATE = True
DEFAULT_AUTOCLEAN_STATE = False

class TGPrompter(Partial):

    def __init__(self,
                 logger: Logger,
                 prompt_logger: Logger,
                 task_manager: TaskManager,
                 runner: PromptRunner):
        self.logger = logger
        self.prompt_logger = prompt_logger
        self.task_manager = task_manager
        self.runner = runner

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.PROMPT_EDIT, MessageState.IDLE]

    async def switch_debug_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        debug = context.user_data.get(DEBUG_KEY, DEFAULT_DEBUG_STATE)
        debug = not debug
        context.user_data[DEBUG_KEY] = debug
        message = "Debug mode is on." if debug else "Debug mode is off."
        self.logger.info(f'/switch_debug_mode / {user.id} / {user.name}: {message}')
        await update.effective_chat.send_message(message)

    async def switch_autoclean(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        autoclean = context.user_data.get(AUTOCLEAN_KEY, DEFAULT_AUTOCLEAN_STATE)
        autoclean = not autoclean
        context.user_data[AUTOCLEAN_KEY] = autoclean
        message = "Autoclean mode is on." if autoclean else "Autoclean mode is off."
        self.logger.info(f'/switch_autoclean / {user.id} / {user.name}: {message}')
        await update.effective_chat.send_message(message)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        user = update.effective_user
        prompt = update.message.text
        context.user_data[PROMPT_KEY] = prompt
        self.logger.info(f'prompting.message / {user.id} / {user.name}: new prompt set\n{prompt}')
        self.prompt_logger.info(f'prompting.message / {user.id} / {user.name}: new prompt set\n{prompt}')
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

    async def prompt_fetch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        prompt = context.user_data.get(PROMPT_KEY, None)
        self.logger.info(f'/prompt_fetch / {user.id} / {user.name}: {len(prompt) if prompt else "nothing"}')
        message = f"No prompt is set" if prompt is None else prompt
        await update.effective_chat.send_message(message)


    async def run_to_score(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        # Fast Demo
        user = update.effective_user
        focus = FocusManagement(context)
        if focus.task is None:
            self.logger.info(f'/run_to_score / {user.id} / {user.name}: no task selected')
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            self.logger.info(f'/run_to_score / {user.id} / {user.name}: no prompt set')
            await update.effective_chat.send_message("Please enter your prompt first.")
            return

        self.logger.info(f'/run_to_score / {user.id} / {user.name}')
        message = await update.effective_chat.send_message('Computing...')
        user_id = tg_user_id(update.effective_user.id)
        result_batch = await self.runner.compute_hidden_batch(task, user_id, prompt)
        self.logger.info(f'/run_to_score / {user.id} / {user.name} / {result_batch.score * 100:.2f}')
        self.prompt_logger.info(f'/run_to_score / {user.id} / {user.name}\n{prompt=}\n\n{result_batch.tg_html_form()=}')
        await message.edit_text(result_batch.tg_html_form_semihidden(), parse_mode='HTML')

        if context.user_data.get(AUTOCLEAN_KEY, DEFAULT_AUTOCLEAN_STATE):
            context.user_data[PROMPT_KEY] = ""

    async def run_open(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        # Fast Demo
        user = update.effective_user
        focus = FocusManagement(context)
        if focus.task is None:
            self.logger.info(f'/run_open / {user.id} / {user.name}: no task selected')
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            self.logger.info(f'/run_open / {user.id} / {user.name}: no prompt set')
            await update.effective_chat.send_message("Please enter your prompt first.")
            return
        context.user_data[STOP_KEY] = False
        debug = context.user_data.get(DEBUG_KEY, DEFAULT_DEBUG_STATE)
        self.logger.info(f'/run_open / {user.id} / {user.name} / {debug = }')
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
                evall = await self.runner.process_snippet(
                    task=task,
                    snippet_id=snippet_id,
                    prompt=prompt,
                    matcher=matcher,
                )
                prefix = f'{idd + 1}/{total}. '
                self.prompt_logger.info(f'/run_open / {user.id} / {user.name} / {prefix + evall.tg_html_form()}')
                await update.effective_chat.send_message(prefix + evall.tg_html_form(), parse_mode='HTML')
            self.logger.info(f'/run_open / {user.id} / {user.name} / {matcher.score() * 100:.2f}')
            await update.effective_chat.send_message(
                f'Total open avg score: {matcher.score() * 100:.2f}',
                parse_mode='HTML'
            )
        if context.user_data.get(AUTOCLEAN_KEY, AUTOCLEAN_KEY):
            context.user_data[PROMPT_KEY] = ""

    async def run_snippet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        focus = FocusManagement(context)
        if focus.task is None:
            self.logger.info(f'/run_snippet / {user.id} / {user.name}: no prompt set')
            await update.effective_chat.send_message("No task selected. Use /task_select to choose one.")
            return
        if focus.snippet is None:
            self.logger.info(f'/run_snippet / {user.id} / {user.name} / {focus.task}: no snippet set')
            await update.effective_chat.send_message("No snippet selected. Use /snippet_focus to choose one.")
            return

        task = self.task_manager.get_current_task(focus.task)
        prompt = context.user_data.get(PROMPT_KEY, "")

        if prompt == "":
            self.logger.info(f'/run_snippet / {user.id} / {user.name} / {focus.task} - {focus.snippet}: no prompt set')
            await update.effective_chat.send_message("Please enter your prompt first.")
            return

        snippet_dct = task.open_snippets.get(focus.snippet, None)
        if snippet_dct is None:
            self.logger.info(f'/run_snippet / {user.id} / {user.name} / {focus.task} - {focus.snippet}: no snippet found')
            await update.effective_chat.send_message("Snippet name seems to be broken. Try another one.")
            return

        self.logger.info(f'/run_snippet / {user.id} / {user.name} / {focus.task} - {focus.snippet}: run')
        await update.effective_chat.send_message(f'Processing Task {focus.task} / Snippet: {focus.snippet}')

        matcher = task.get_matcher()
        evall = await self.runner.process_snippet(
            task=task,
            snippet_id=focus.snippet,
            prompt=prompt,
            matcher=matcher,
        )
        self.logger.info(f'/run_snippet / {user.id} / {user.name} / {evall.score * 100:.2f}')
        self.prompt_logger.info(f'/run_snippet / {user.id} / {user.name} / {evall.tg_html_form()}')
        await update.effective_chat.send_message(evall.tg_html_form(), parse_mode='HTML')