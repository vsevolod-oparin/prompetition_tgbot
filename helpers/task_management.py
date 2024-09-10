from typing import List

from pathlib import Path
import argparse
import gradio as gr
import os
import json

from core.utils import from_txt_file, to_txt_file


def parse_args(input_string: List[str] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update vector base")
    parser.add_argument(
        "--data_root",
        type=str,
        default='data',
        help="Path to vector base directory"
    )
    return parser.parse_args(input_string)


class DataOperator:

    def __init__(self, data_root):
        self.data_root = Path(data_root)

    def fetch_tasks(self):
        return [f.name for f in self.data_root.iterdir() if f.is_dir()]

    def fetch_snippets(self, task_name):
        task_dir = self.data_root / task_name / 'snippets'
        return list(sorted([
            snippet.name
            for snippet in task_dir.iterdir()
            if snippet.is_dir()
        ]))

    def update_snippets(self, task_name):
        snippets = self.fetch_snippets(task_name)
        snippet_choice = snippets[0]

        return gr.update(choices=snippets, value=snippet_choice), *self.update_content(task_name, snippet_choice)

    def update_content(self, task_name, snippet):
        snippet_dir = self.data_root / task_name / 'snippets' / snippet
        task_txt = from_txt_file(snippet_dir / 'task.txt')
        answer_txt = from_txt_file(snippet_dir / 'answer.json')
        return task_txt, answer_txt

    def save_content(self, task_name, snippet_name, task_data, answer_data):
        snippet_dir = self.data_root / task_name / 'snippets' / snippet_name
        try:
            json.loads(answer_data)
        except:
            raise gr.Error(message=f'Incorrect json: {answer_data}', duration=3)
        to_txt_file(snippet_dir / 'task.txt', task_data)
        to_txt_file(snippet_dir / 'answer.json', answer_data)
        return gr.Info('Success', duration=1)

    def create_new_one(self, task_name, new_snippet, task_data, answer_data):
        new_snippet = new_snippet.strip()
        if not new_snippet:
            raise gr.Error(message=f'No new name', duration=1)
        snippet_dir = self.data_root / task_name / 'snippets' / new_snippet
        if snippet_dir.exists():
            raise gr.Error(message=f'{new_snippet} already exists', duration=1)
        snippet_dir.mkdir(parents=True)

        self.save_content(task_name, new_snippet, task_data, answer_data)
        snippets = self.fetch_snippets(task_name)
        return gr.update(choices=snippets, value=new_snippet)



def main(args: argparse.Namespace):
    data_root = Path(args.data_root)
    operator = DataOperator(data_root)

    with gr.Blocks() as demo:
        with gr.Column():
            with gr.Row():
                task_dropdown = gr.Dropdown(choices=operator.fetch_tasks(), label="Select Folder")
                snippet_dropdown = gr.Dropdown(choices=[], label="Select Snippet")

            task_content = gr.Textbox(label="Task Content", interactive=True)
            answer_content = gr.Textbox(label="Answer Content", interactive=True)
            save_button = gr.Button('Save', variant='primary')

            with gr.Row():
                new_snippet = gr.Textbox(label='', max_lines=1)
                new_one = gr.Button('Create new one...')

        task_dropdown.change(operator.update_snippets, task_dropdown, [snippet_dropdown, task_content, answer_content])
        snippet_dropdown.change(operator.update_content, [task_dropdown, snippet_dropdown], [task_content, answer_content])
        save_button.click(operator.save_content, [task_dropdown, snippet_dropdown, task_content, answer_content])
        new_one.click(operator.create_new_one, [task_dropdown, new_snippet, task_content, answer_content], snippet_dropdown)
        # interface = gr.Interface(fn=lambda: "Select a folder and snippet", inputs=[], outputs="text")

    demo.launch(show_error=True)

if __name__ == '__main__':
    main(parse_args())
