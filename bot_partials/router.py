from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.partial import Partial


class MessageRouter(Partial):

    def __init__(self, partials: List[Partial], default_partial: Partial):
        self.routes = {
            state: p
            for p in partials
            for state in p.message_states
        }
        self.default = default_partial

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_state = context.user_data['state']
        if current_state in self.routes:
            await self.routes[current_state].message(update, context)
        else:
            await self.default.message(update, context)
