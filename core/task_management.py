import argparse
from pathlib import Path
from typing import List

from core.task import PromptTask
from core.utils import from_json_file


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
        task_pths = [
            task_dir / 'info.json'
            for task_dir in self.data_root.glob('*')
            if (task_dir / 'info.json').exists()
        ]
        task_objs = [from_json_file(task_pth) for task_pth in task_pths]
        task_objs = [obj for obj in task_objs if obj.get('exposed', True)]
        return task_objs

    def get_current_task(self, task_id: str) -> PromptTask:
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
