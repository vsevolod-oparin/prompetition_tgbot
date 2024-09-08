import json
import traceback
from logging import Logger

from telegram import Update
from telegram.ext import ContextTypes

class TGErrorHandler:
    def __init__(self, logger: Logger):
        self.logger = logger

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a telegram message to notify the developer."""
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"update = {json.dumps(update_str, indent=2, ensure_ascii=False)}\n\n"
            f"context.user_data = {str(context.user_data)}\n\n"
            f"{tb_string}"
        )
        self.logger.error(message)

        await update.effective_user.send_message("Oops, something went wrong.")
