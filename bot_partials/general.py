from typing import List

from bot_partials.partial import Partial
from bot_partials.state import MessageState
from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.userdata_keys import USER_NAME_KEY, STATE_KEY
from core.prompt_db import PromptDBManager
from core.utils import from_txt_file, tg_user_id


class TGBotGeneral(Partial):

    def __init__(self, sql_db: PromptDBManager):
        self.sql_db = sql_db

    @property
    def message_states(self) -> List[MessageState]:
        return [MessageState.EXPECTING_NAME]

    # Define a few command handlers. These usually take the two arguments update and
    # context.
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.effective_chat.send_message(from_txt_file('templates/greetings.txt'))
        context.user_data[STATE_KEY] = MessageState.EXPECTING_NAME
        if USER_NAME_KEY not in context.user_data:
            await update.effective_chat.send_message('Before running the bot, please set your name:')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.effective_chat.send_message(from_txt_file('templates/help.txt'))

    async def whoami(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        name = context.user_data.get(USER_NAME_KEY, None)
        message = name or "No name has been found."
        await update.effective_chat.send_message(message)

    async def set_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        tokens = update.message.text.strip().split(' ')
        if len(tokens) > 1:
            name = ' '.join(tokens[1:])
            context.user_data[USER_NAME_KEY] = name
            self.sql_db.update_user_name(tg_user_id(update.effective_user.id), name)
            context.user_data[STATE_KEY] = MessageState.IDLE
            await update.effective_chat.send_message(
                f"Ok, now your name is stored as <b>{name}</b>. You can change it with /set_name.",
                parse_mode='HTML',
            )
        else:
            context.user_data[STATE_KEY] = MessageState.EXPECTING_NAME
            await update.effective_chat.send_message("Ok, now type your name in:")

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        if context.user_data[STATE_KEY] == MessageState.EXPECTING_NAME:
            name = update.message.text.strip()
            if name:
                context.user_data[USER_NAME_KEY] = name
                self.sql_db.update_user_name(tg_user_id(update.effective_user.id), name)
                context.user_data[STATE_KEY] = MessageState.IDLE
                await update.effective_chat.send_message(
                    f"Ok, now your name is stored as <b>{name}</b></>. You can change it with /set_name.",
                    parse_mode='HTML'
                )
            else:
                await update.effective_chat.send_message(
                    f"Can't see the name. Try again."
                )