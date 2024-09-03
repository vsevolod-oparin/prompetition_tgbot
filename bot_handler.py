import argparse
import json
from pathlib import Path


from telegram import ForceReply, Update, ChatFullInfo, UserProfilePhotos
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


class TGBotHandler:

    def __init__(self, args: argparse.Namespace):
        self.data_root = Path(args.data_root)

    ######################
    #  GENERAL MESSAGES  #
    ######################

    # Define a few command handlers. These usually take the two arguments update and
    # context.
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.message.reply_text('Started')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("Help!")

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        await update.message.reply_text(update.message.text)


