import json
from pathlib import Path
from typing import Dict

from core.matcher import AvgIoUMatcher, matcher_from_name
from core.transform_pipe import TransformPipe
from core.utils import from_json_file, from_txt_file, PathLike, html_escape
from jinja2 import Environment, FileSystemLoader


class PromptTask:

    def __init__(self, task_dir: PathLike):
        self.task_dir = Path(task_dir)

        self.task_info_pth = self.task_dir / 'info.json'
        self.task_info = from_json_file(self.task_info_pth)

        reply_pipe_config = self.task_info['reply_pipe']
        self.reply_pipe = TransformPipe(reply_pipe_config, answer_type=self.answer_type)

        answer_pipe_config = self.task_info['answer_pipe']
        self.answer_pipe = TransformPipe(answer_pipe_config, answer_type=self.answer_type)

    def get_matcher(self):
        return matcher_from_name(self.task_info['matcher'])

    @property
    def sample_prompt(self) -> str:
        prompt_pth = self.task_dir / self.task_info["sample_prompt_pth"]
        return from_txt_file(prompt_pth)

    @property
    def answer_type(self) -> str:
        return self.task_info['answer_type']

    @property
    def exposed(self) -> bool:
        return self.task_info['exposed']

    @property
    def id(self):
        return self.task_info['id']

    @property
    def description(self):
        return self.task_info['description']

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
            description=self.description,
            sample_prompt=html_escape(self.sample_prompt),
            open_snippets={
                k: json.dumps(obj, indent=2)
                for k, obj in self.open_snippets.items()
            },
            hidden_snippets={
                k: json.dumps(obj, indent=2)
                for k, obj in self.hidden_snippets.items()
            }
        )

    def get_snippets(self, snippet_type):
        result = dict()
        for snippet in self.task_info[snippet_type]:
            snippet = Path(snippet)
            txt_pth = self.task_dir / snippet / 'task.txt'
            answer_pth = self.task_dir / snippet / 'answer.json'
            result[snippet.name] = {
                'txt': from_txt_file(txt_pth),
                'answer': from_json_file(answer_pth)
            }
        return result


if __name__ == '__main__':
    task = PromptTask('data/humor')
    print(task)