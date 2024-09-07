import dataclasses
import json
from typing import Any, Dict, List

from chromadb.rate_limiting import rate_limit
from openai import AsyncOpenAI

from core.ai import get_ai_response
from core.matcher import Matcher
from core.ratelimit import RateLimiter, RateLimitedBatchQueue
from core.task import PromptTask
from core.utils import html_escape


def data_to_str(data):
    if isinstance(data, str):
        return data
    if isinstance(data, Dict):
        return json.dumps(data, indent=2)
    return data


@dataclasses.dataclass
class SnippetEvaluation:
    task_id: str
    snippet_id: str
    score: float
    snippet_txt: str
    result_data: Any
    answer_data: Any
    result_msg: str

    def tg_html_form(self) -> str:
        return "\n".join([
            f'Score: <b>{self.score * 100.0:.2f}%</b>',
            f'Text:\n<code>{html_escape(self.snippet_txt)}</code>',
            f'Result:\n<code>{data_to_str(self.result_data)}</code>',
            f'Answer:\n<code>{data_to_str(self.answer_data)}</code>',
            f'Result message:\n<code>### BEGIN ###\n{html_escape(self.result_msg)}\n### END ###</code>'
        ])


@dataclasses.dataclass
class SnippetBatchEvaluation:
    task_id: str
    tag: str
    score: float
    eval_list: List[SnippetEvaluation]

    def tg_html_form(self) -> str:
        title = self.task_id if self.tag is None else f'{self.task_id}/{self.tag}'
        lines = [
            f'<b>{title} - score: {self.score * 100:.2f}%</b>',
        ]
        for idd, evall in enumerate(self.eval_list):
            lines.append(f"{idd + 1}. {evall.snippet_id} {evall.tg_html_form()}")

        return '\n'.join(lines)

    def tg_html_form_semihidden(self) -> str:
        title = self.task_id if self.tag is None else f'{self.task_id}/{self.tag}'
        lines = [
            f'<b>{title} - score: {self.score * 100:.2f}%</b>',
            '<code>',
        ]
        for idd, evall in enumerate(self.eval_list):
            lines.extend([
                f'{idd + 1}. Snippet {evall.snippet_id}',
                f'  score: {evall.score * 100:.2f}%',
            ])
        lines.append('</code>')
        return '\n'.join(lines)

    def tg_html_shortform(self) -> str:
        title = self.task_id if self.tag is None else f'{self.task_id}/{self.tag}'
        return f'<b>{title} - score: {self.score * 100:.2f}%</b>'


class PromptRunner:

    def __init__(self, aclient: AsyncOpenAI, rate_limiter: RateLimiter, queue: RateLimitedBatchQueue):
        self.aclient = aclient
        self.rate_limiter = rate_limiter
        self.queue = queue

    async def process_snippet(self,
                              task: PromptTask,
                              snippet_id: str,
                              prompt: str,
                              matcher: Matcher,
                              custom_snippet_dct: Dict = None) -> SnippetEvaluation:
        task_snippet_dcts = custom_snippet_dct or task.open_snippets
        snippet_dct = task_snippet_dcts[snippet_id]
        snippet_txt = snippet_dct['Task']
        snippet_answer = snippet_dct['Answer']
        result_msg = await self.rate_limiter.submit(get_ai_response(
            client=self.aclient,
            system_prompt=prompt,
            prompt=snippet_txt
        ))
        result_data = task.reply_pipe(result_msg)
        answer_data = task.answer_pipe(snippet_answer)
        score = matcher.accumulate(result_data, answer_data)
        return SnippetEvaluation(
            task_id=task.id,
            snippet_id=snippet_id,
            score=score,
            result_data=result_data,
            answer_data=answer_data,
            snippet_txt=snippet_txt,
            result_msg=result_msg
        )

    async def compute_task_batch(self,
                                 task: PromptTask,
                                 snippet_dct: Dict,
                                 prompt: str,
                                 tag: str = None):
        matcher = task.get_matcher()
        tasks = []
        for snippet_id in snippet_dct:
            tasks.append(self.process_snippet(task, snippet_id, prompt, matcher, snippet_dct))
        eval_list = await self.queue.add_batch_task(tasks)
        return SnippetBatchEvaluation(
            score=matcher.score(),
            task_id=task.id,
            eval_list=eval_list,
            tag=tag
        )

    async def compute_open_batch(self, task: PromptTask, prompt: str):
        return await self.compute_task_batch(
            task=task,
            snippet_dct=task.open_snippets,
            prompt=prompt,
            tag="open"
        )

    async def compute_hidden_batch(self, task: PromptTask, prompt: str):
        return await self.compute_task_batch(
            task=task,
            snippet_dct=task.hidden_snippets,
            prompt=prompt,
            tag="hidden"
        )