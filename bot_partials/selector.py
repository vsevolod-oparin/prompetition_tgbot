import argparse
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.partial import Partial
from bot_partials.state import MessageState
from core.task import PromptTask
from core.utils import html_escape, from_json_file

class FocusManagement:

    def __init__(self, context: ContextTypes.DEFAULT_TYPE):
        self.context = context
        self.task = context.user_data.get('task', None)
        self.snippet = context.user_data.get('snippet', None)

    def update_context(self):
        self.context.user_data['task'] = self.task
        self.context.user_data['snippet'] = self.snippet

    def update_task(self, new_task):
        if self.task == new_task:
            return
        self.task = new_task
        self.snippet = None
        self.update_context()

    def update_snippet(self, new_snippet):
        if self.snippet == new_snippet:
            return
        self.snippet = new_snippet
        self.update_context()

    def unselect_task(self):
        self.task = None
        self.snippet = None
        self.update_context()

    def unselect_snippet(self):
        self.snippet = None
        self.update_context()


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
        return [MessageState.TASK_SELECTION, MessageState.SNIPPET_SELECTION]

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
        focus = FocusManagement(context)
        choices = []
        for idd, pth in self.get_task_id_map().items():
            if search_token in idd:
                choices.append(idd)
        choice_num = len(choices)
        if choice_num == 0:
            await update.effective_user.send_message(f'No task found with id {search_token}.')
            context.user_data['state'] = MessageState.TASK_SELECTION
        elif choice_num == 1:
            focus.update_task(choices[0])
            context.user_data['state'] = MessageState.IDLE
            await update.effective_user.send_message(f'Task `{choices[0]}` has been selected.')
        else:
            multi_choice = "\n- ".join(choices)
            suffix = "No task selected." if focus.task is None else f"Current task stays: {focus.task}"
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

    async def _get_task_or_complain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *, if_not: str) -> Optional[PromptTask]:
        focus = FocusManagement(context)
        if focus.task is None:
            await update.effective_user.send_message(if_not)
            return None
        return self.get_current_task(focus.task)

    async def snippet_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To see the snippets, you must select a task first. Use /select command.",
        )
        if current_task is None:
            return

        snippets = current_task.open_snippets
        title = f'<b>{html_escape(current_task.title_with_id)}</b>'
        snippet_lines = [f'- <b>{name}</b>: {html_escape(obj["Task"])}' for name, obj in snippets.items()]
        all_lins = [title, ''] + snippet_lines
        await update.effective_user.send_message('\n'.join(all_lins), parse_mode='HTML')

    async def _select_snippet(self, search_token: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To select the snippet, you must select a task first. Use /select command.",
        )
        if current_task is None:
            return

        focus = FocusManagement(context)
        snippets_names = current_task.open_snippets.keys()
        choices = []
        for name in snippets_names:
            if search_token in name:
                choices.append(name)
        choice_num = len(choices)
        if choice_num == 0:
            await update.effective_user.send_message(f'No snippet found with id {search_token}.')
            context.user_data['state'] = MessageState.SNIPPET_SELECTION
        elif choice_num == 1:
            focus.update_snippet(choices[0])
            context.user_data['state'] = MessageState.IDLE
            await update.effective_user.send_message(f'Task `{choices[0]}` has been selected.')
        else:
            multi_choice = "\n- ".join(choices)
            suffix = "No snippet selected." if focus.snippet is None else f"Current snippet is {focus.snippet}"
            await update.effective_user.send_message(
                ' '.join([
                    f'Multiple snippets found:\n- {multi_choice}.',
                    suffix
                ])
            )
            context.user_data['state'] = MessageState.SNIPPET_SELECTION

    async def snippet_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        search_token = update.message.text.strip()
        search_token = ' '.join(search_token.split(' ')[1:])
        if search_token == "":
            await update.message.reply_text('Select the snippet by typing snippet id.')
            context.user_data['state'] = MessageState.SNIPPET_SELECTION
        else:
            await self._select_snippet(search_token, update, context)

    async def snippet_unfocus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        focus = FocusManagement(context)
        if focus.snippet is None:
            await update.effective_user.send_message(f'No snippet to unselect.')
            return

        old_snippet = focus.snippet
        focus.update_snippet(None)
        await update.effective_user.send_message(f'Snippet `{old_snippet}` has been unselected.')

    async def show_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        current_task = await self._get_task_or_complain(
            update,
            context,
            if_not="To see the task, select a task first. Use /select command.",
        )
        if current_task is None:
            return
        focus = FocusManagement(context)
        await update.effective_user.send_message(current_task.short_description(snippet=focus.snippet), parse_mode='HTML')

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data['state'] == MessageState.TASK_SELECTION:
            search_token = update.message.text.strip()
            await self._select_task(search_token, update, context)
        elif context.user_data['state'] == MessageState.SNIPPET_SELECTION:
            search_token = update.message.text.strip()
            await self._select_snippet(search_token, update, context)
        else:
            context.user_data['state'] = MessageState.IDLE



