from pathlib import Path
from typing import Dict

from core.utils import from_json_file, from_txt_file, PathLike
from jinja2 import Environment, FileSystemLoader


class PromptTask:

    def __init__(self, task_dir: PathLike):
        self.task_dir = Path(task_dir)

        self.task_info_pth = self.task_dir / 'info.json'
        self.task_info = from_json_file(self.task_info_pth)

    @property
    def id(self):
        return self.task_info['id']

    @property
    def title(self):
        return self.task_info['title']

    @property
    def open_snippets(self) -> Dict:
        return self.get_snippets('open_snippets')

    @property
    def hidden_snippets(self) -> Dict:
        return self.get_snippets('hidden_snippets')

    def __repr__(self) -> str:
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('full_task.txt')
        return template.render(
            id=self.id,
            title=self.title,
            open_snippets=self.open_snippets,
            hidden_snippets=self.hidden_snippets
        )

    def get_snippets(self, snippet_type):
        result = dict()
        for snippet in self.task_info[snippet_type]:
            snippet = Path(snippet)
            txt_pth = self.task_dir / snippet / 'task.txt'
            result[snippet.name] = from_txt_file(txt_pth)
        return result


if __name__ == '__main__':
    task = PromptTask('data/humor')
    print(task)