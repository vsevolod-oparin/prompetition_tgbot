from enum import Enum


class MessageState(Enum):
    IDLE              = 0

    # Selection
    TASK_SELECTION    = 1
    SNIPPET_SELECTION = 2

    # Prompting
    PROMPT_EDIT       = 3