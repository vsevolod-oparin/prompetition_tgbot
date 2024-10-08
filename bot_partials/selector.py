from collections import defaultdict
from logging import Logger
from typing import List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.focus import FocusManagement
from bot_partials.partial import Partial
from bot_partials.state import MessageState
from bot_partials.userdata_keys import STATE_KEY
from core.task_management import TaskManager
from core.task import PromptTask
from core.utils import html_escape


class TGSelector(Partial):

    def __init__(self, logger: Logger, task_manager: TaskManager):
        self.logger = logger
        self.task_manager = task_manager

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.TASK_SELECTION, MessageState.SNIPPET_SELECTION]

    async def task_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        task_conf_list = self.task_manager.fetch_task_conf_list()
        result_dct = defaultdict(list)
        for task_obj in task_conf_list:
            lang = task_obj['lang']
            result_dct[lang].append(f'- {task_obj["title"]} ({task_obj["id"]})')

        self.logger.info(f'/task_list / {user.id} / {user.name}: num of tasks {len(task_conf_list)}')

        result_lst = []
        for lang, lst in result_dct.items():
            result_lst.append(f'<b>{lang.upper()}</b>')
            result_lst.append('\n'.join(lst))
            result_lst.append('')
        first_id = task_conf_list[0]["id"]
        result_lst.append(f'Use command /task_select, to choose a particular task. E.g. "/task_select {first_id}"')

        await update.message.reply_text('\n'.join(result_lst).strip(), parse_mode='HTML')

    async def _select_task(self, search_token: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        focus = FocusManagement(context)
        choices = self.task_manager.search_tasks(search_token)
        choice_num = len(choices)

        if choice_num == 0:
            self.logger.info(f'/task_select / {user.id} / {user.name} / {search_token}: no tasks found.')
            await update.effective_chat.send_message(f'No task found with id {search_token}.')
            context.user_data[STATE_KEY] = MessageState.TASK_SELECTION
        elif choice_num == 1:
            focus.update_task(choices[0])
            self.logger.info(f'/task_select / {user.id} / {user.name} / {search_token}: single task {choices[0]}.')
            context.user_data[STATE_KEY] = MessageState.IDLE
            await update.effective_chat.send_message(f'Task `{choices[0]}` has been selected.')
            current_task = self.task_manager.get_current_task(focus.task)
            await update.effective_chat.send_message(current_task.short_description(), parse_mode='HTML')
        else:
            self.logger.info(f'/task_select / {user.id} / {user.name} / {search_token}: multiple tasks {len(choices)}.')
            multi_choice = "\n- ".join(choices)
            suffix = "\nNo task selected." if focus.task is None else f"\nCurrent task stays: {focus.task}"
            await update.effective_chat.send_message(
                ' '.join([
                    f'Multiple tasks found:\n- {multi_choice}.',
                    suffix
                ])
            )
            context.user_data[STATE_KEY] = MessageState.TASK_SELECTION

    async def select_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_token = update.message.text.strip()
        search_token = ' '.join(search_token.split(' ')[1:])
        if search_token == "":
            await update.message.reply_text('Select the task by typing id')
            context.user_data[STATE_KEY] = MessageState.TASK_SELECTION
        else:
            await self._select_task(search_token, update, context)

    async def _get_task_or_complain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *, if_not: str) -> Optional[PromptTask]:
        focus = FocusManagement(context)
        if focus.task is None:
            await update.effective_chat.send_message(if_not)
            await self.task_list(update, context)
            return None
        return self.task_manager.get_current_task(focus.task)

    async def snippet_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.logger.info(f'/snippet_list / {user.id} / {user.name}')
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To see the snippets, you must select a task first. Use /snippet_focus command.",
        )
        if current_task is None:
            return

        snippets = current_task.open_snippets
        title = f'<b>{html_escape(current_task.title_with_id)}</b>'
        snippet_lines = [f'- <b>{name}</b>: {html_escape(obj["Task"])}' for name, obj in snippets.items()]
        all_lins = [title, ''] + snippet_lines
        await update.effective_chat.send_message('\n'.join(all_lins), parse_mode='HTML')

    async def _select_snippet(self, search_token: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To select the snippet, you must select a task first. Use /snippet_focus command.",
        )
        if current_task is None:
            self.logger.info(f'/snippet_focus / {user.id} / {user.name}: no task')
            return

        focus = FocusManagement(context)
        choices = self.task_manager.search_snippet(search_token, current_task)
        choice_num = len(choices)

        if choice_num == 0:
            self.logger.info(f'/snippet_focus / {user.id} / {user.name} / {focus.task} - {search_token}: no snippet found')
            await update.effective_chat.send_message(f'No snippet found with id {search_token}.')
            context.user_data[STATE_KEY] = MessageState.SNIPPET_SELECTION
        elif choice_num == 1:
            focus.update_snippet(choices[0])
            self.logger.info(
                f'/snippet_focus / {user.id} / {user.name} / {focus.task} - {search_token}: snippet selected {choices[0]}'
            )
            context.user_data[STATE_KEY] = MessageState.IDLE
            await update.effective_chat.send_message(f'Task `{choices[0]}` has been selected.')
        else:
            self.logger.info(
                f'/snippet_focus/ {user.id} / {user.name} / {focus.task} - {search_token}: multiple snippets {len(choices)}'
            )
            multi_choice = "\n- ".join(choices)
            suffix = "No snippet selected." if focus.snippet is None else f"Current snippet is {focus.snippet}"
            await update.effective_chat.send_message(
                ' '.join([
                    f'Multiple snippets found:\n- {multi_choice}.',
                    suffix
                ])
            )
            context.user_data[STATE_KEY] = MessageState.SNIPPET_SELECTION

    async def snippet_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_token = update.message.text.strip()
        search_token = ' '.join(search_token.split(' ')[1:])
        if search_token == "":
            await update.message.reply_text('Select the snippet by typing snippet id.')
            context.user_data[STATE_KEY] = MessageState.SNIPPET_SELECTION
        else:
            await self._select_snippet(search_token, update, context)

    async def snippet_unfocus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        focus = FocusManagement(context)
        self.logger.info(
            f'/snippet_unfocus / {user.id} / {user.name} / {focus.task} - {focus.snippet}'
        )
        if focus.snippet is None:
            await update.effective_chat.send_message(f'No snippet to unselect.')
            return

        old_snippet = focus.snippet
        focus.update_snippet(None)
        await update.effective_chat.send_message(f'Snippet `{old_snippet}` has been unselected.')

    async def show_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        """Send a message when the command /start is issued."""
        focus = FocusManagement(context)
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To see the task, select a task first. Running /task_list the see the choices.",
        )
        if current_task is None:
            self.logger.info(
                f'/task_show / {user.id} / {user.name} / {focus.task} - {focus.snippet}: no task to show'
            )
            return
        self.logger.info(
            f'/task_show / {user.id} / {user.name} / {focus.task} - {focus.snippet}'
        )
        await update.effective_chat.send_message(current_task.short_description(snippet=focus.snippet), parse_mode='HTML')

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if context.user_data[STATE_KEY] == MessageState.TASK_SELECTION:
            search_token = update.message.text.strip()
            await self._select_task(search_token, update, context)
        elif context.user_data[STATE_KEY] == MessageState.SNIPPET_SELECTION:
            search_token = update.message.text.strip()
            await self._select_snippet(search_token, update, context)
        else:
            context.user_data[STATE_KEY] = MessageState.IDLE



