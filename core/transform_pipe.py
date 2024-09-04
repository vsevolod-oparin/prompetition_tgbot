import json
from typing import Dict, List


class ValueTransformer:

    def __init__(self, *, strip: bool = True):
        self.strip = strip

    def text_preprocess(self, value: str) -> str:
        if self.strip:
            return value.strip()
        return value


class LastChunk(ValueTransformer):
    NAME = 'last_chunk'

    def __init__(self, *, separator: str, strip: bool = True):
        super().__init__(strip=strip)
        self.separator = separator

    def __call__(self, value):
        value = self.text_preprocess(value)
        if value == "":
            return value
        return value.split(self.separator)[-1]


class FromJson(ValueTransformer):
    NAME = 'from_json'

    def __init__(self, *, strip: bool = True):
        super().__init__(strip=strip)

    def __call__(self, value):
        value = self.text_preprocess(value)
        if value == "":
            return None
        return json.loads(value)


class LineSplit(ValueTransformer):
    NAME = 'line_split'

    def __init__(self, *, strip: bool = True):
        super().__init__(strip=strip)

    def __call__(self, value):
        value = self.text_preprocess(value)
        if value == "":
            return []
        return value.split('\n')


class ToAnswer(ValueTransformer):
    NAME = 'to_answer_type'

    def __init__(self, *, answer_type: str):
        super().__init__(strip=False)
        self.answer_type = answer_type

    def __call__(self, value):
        if self.answer_type == 'set':
            return set(value)
        if self.answer_type == 'list':
            return list(value)
        if self.answer_type == 'str':
            return str(value)
        if self.answer_type == 'json_str':
            return json.dumps(value)
        raise RuntimeError(f'Unknown type of answer: {self.answer_type}')


TRANSFORM_DICT = {
    ToAnswer.NAME: ToAnswer,
    LastChunk.NAME: LastChunk,
    LineSplit.NAME: LineSplit,
    FromJson.NAME: FromJson,
}

class TransformPipe:

    def __init__(self, transform_config: List[Dict], answer_type: str):
        self.transform_list = []
        for config in transform_config:
            ttype = config['type']
            args = config.copy()
            args.pop('type')
            if ttype == ToAnswer.NAME:
                args['answer_type'] = answer_type
            transform = TRANSFORM_DICT[ttype](**args)
            self.transform_list.append(transform)

    def __call__(self, value):
        for t in self.transform_list:
            value = t(value)
        return value
