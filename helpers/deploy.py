import shutil
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
        "--deploy_dir",
        type=str,
        default='deploy',
        help="Path to vector base directory"
    )
    return parser.parse_args(input_string)

def main(args: argparse.Namespace):
    deploy_dir = Path(args.deploy_dir)
    deploy_dir.mkdir(parents=True, exist_ok=True)

    copy_targets = [
        'bot_partials',
        'core',
        'data',
        'templates',
        'bot.py',
        'requirements.txt'
    ]

    creatable_dirs = [
        'persistence',
        'logs',
    ]

    for entity in copy_targets:
        target_entity = deploy_dir / entity
        source_entity = Path('.') / entity
        if source_entity.is_dir():
            if target_entity.exists():
                shutil.rmtree(target_entity)
            shutil.copytree(source_entity, target_entity)
        else:
            if target_entity.exists():
                target_entity.unlink()
            shutil.copy(source_entity, target_entity)


    for new_dir in creatable_dirs:
        (deploy_dir / new_dir).mkdir(exist_ok=True, parents=True)


if __name__ == '__main__':
    main(parse_args())
