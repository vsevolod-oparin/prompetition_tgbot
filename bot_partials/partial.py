from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.state import MessageState


class Partial:

    @property
    def message_states(self) -> List[MessageState]:
        return []

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass