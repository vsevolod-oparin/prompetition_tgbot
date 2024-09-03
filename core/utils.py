import json
from pathlib import Path
from typing import Union, Any

PathLike = Union[str, Path]

def from_txt_file(filepath: PathLike):
    with open(filepath, 'r') as f:
        return f.read()

def from_json_file(filepath: PathLike):
    with open(filepath, 'r') as f:
        return json.load(f)


def to_json_file(filepath: PathLike, data: Any):
    with open(filepath, 'w') as f:
        data_str = json.dumps(data, indent=2)
        f.write(data_str)