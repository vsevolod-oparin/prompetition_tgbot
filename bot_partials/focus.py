from telegram.ext import ContextTypes


class FocusManagement:

    def __init__(self, context: ContextTypes.DEFAULT_TYPE):
        self.context = context
        self.task = context.user_data.get('task', None)
        self.snippet = context.user_data.get('snippet', None)

    def update_context(self):
        self.context.user_data['task'] = self.task
        self.context.user_data['snippet'] = self.snippet

    def update_task(self, new_task):
        if self.task == new_task:
            return
        self.task = new_task
        self.snippet = None
        self.update_context()

    def update_snippet(self, new_snippet):
        if self.snippet == new_snippet:
            return
        self.snippet = new_snippet
        self.update_context()

    def unselect_task(self):
        self.task = None
        self.snippet = None
        self.update_context()

    def unselect_snippet(self):
        self.snippet = None
        self.update_context()