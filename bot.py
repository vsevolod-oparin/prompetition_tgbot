#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import argparse
import logging
import os
from typing import List

from telegram import ForceReply, Update, ChatFullInfo, UserProfilePhotos
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, PicklePersistence

from bot_handler import TGBotHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def parse_args(input_string: List[str] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update vector base")
    parser.add_argument(
        "--data_root",
        type=str,
        default='data',
        help="Path to vector base directory"
    )
    return parser.parse_args(input_string)


def main(args) -> None:
    """Start the bot."""

    bot_handler = TGBotHandler(args)
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath=f"{args.data_root}/prompetition_bot")
    application = (Application.builder()
                   .token(os.environ.get("TG_TOKEN"))
                   .persistence(persistence)
                   .build())

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", bot_handler.start))
    application.add_handler(CommandHandler("help", bot_handler.help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main(parse_args())
