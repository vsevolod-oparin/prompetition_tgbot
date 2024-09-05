import argparse
from pathlib import Path
from typing import List

from anyio import get_current_task
from telegram.ext import ContextTypes

from core.task import PromptTask
from core.utils import from_json_file

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


class TaskManager:

    def __init__(self, args: argparse.Namespace):
        self.data_root = Path(args.data_root)

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

    def fetch_task_conf_list(self):
        return [
            task_dir / 'info.json'
            for task_dir in self.data_root.glob('*')
            if (task_dir / 'info.json').exists()
        ]

    def get_current_task_by_focus(self, focus: FocusManagement) -> PromptTask:
        task_pth = self.get_task_id_map()[focus.task]
        return PromptTask(Path(task_pth).parent)

    def get_current_task_by_id(self, task_id: str) -> PromptTask:
        task_pth = self.get_task_id_map()[task_id]
        return PromptTask(Path(task_pth).parent)

    def search_tasks(self, search_token: str) -> List[str]:
        choices = []
        for idd, pth in self.get_task_id_map().items():
            if search_token in idd:
                choices.append(idd)
        return choices

    @staticmethod
    def search_snippet(search_token: str, task: PromptTask = None):
        snippets_names = task.open_snippets.keys()
        choices = []
        for name in snippets_names:
            if search_token in name:
                choices.append(name)
        return choices
