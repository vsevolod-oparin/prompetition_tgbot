import json
from importlib.resources import contents
from pathlib import Path
from typing import Union, Any

PathLike = Union[str, Path]

def from_txt_file(filepath: PathLike):
    with open(filepath, 'r') as f:
        return f.read()

def to_txt_file(filepath: PathLike, content: str):
    with open(filepath, 'w') as f:
        f.write(content)

def from_json_file(filepath: PathLike):
    with open(filepath, 'r') as f:
        return json.load(f)


def to_json_file(filepath: PathLike, data: Any):
    with open(filepath, 'w') as f:
        data_str = json.dumps(data, indent=2)
        f.write(data_str)


def html_escape(msg: str) -> str:
    return msg \
        .replace('&', '&amp;') \
        .replace('<', '&lt;') \
        .replace('>', '&gt;')

def html_escape_obj(obj):
    if isinstance(obj, list):
        return [html_escape_obj(o) for o in obj]
    elif isinstance(obj, dict):
        return {
            html_escape(k): html_escape_obj(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, str):
        return html_escape(obj)
    else:
        return obj

def tg_user_id(id) -> str:
    return f'TG:{id}'
