from typing import List

from bot_partials.partial import Partial
from bot_partials.state import MessageState
from telegram import Update
from telegram.ext import ContextTypes

from core.utils import from_txt_file


class TGBotGeneral(Partial):

    def __init__(self):
        pass

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.EXPECTING_NAME]

    # Define a few command handlers. These usually take the two arguments update and
    # context.
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.effective_user.send_message(from_txt_file('templates/greetings.txt'))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.effective_user.send_message(from_txt_file('templates/help.txt'))

    async def set_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        context.user_data['state'] = MessageState.EXPECTING_NAME
        await update.effective_user.send_message("Ok, now type your name in:")

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        if context.user_data['state'] == MessageState.EXPECTING_NAME:
            name = update.message.text.strip()
            context.user_data['user_name'] = name
            await update.effective_user.send_message(f"Ok, now your name is stored as {name}")