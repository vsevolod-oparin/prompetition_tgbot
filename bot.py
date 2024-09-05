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

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, PicklePersistence

from bot_partials.general import TGBotGeneral
from bot_partials.prompting import TGBotHandler
from bot_partials.router import MessageRouter
from bot_partials.selector import TGSelector
from core.task_management import TaskManager

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
    parser.add_argument(
        "--persistence_dir",
        type=str,
        default='persistence',
        help="Path to vector base directory"
    )
    return parser.parse_args(input_string)


def main(args) -> None:
    """Start the bot."""

    task_manager = TaskManager(args)

    bot_general = TGBotGeneral()
    bot_handler = TGBotHandler(task_manager)
    bot_selector = TGSelector(task_manager)

    bot_router = MessageRouter(
        partials=[
            bot_selector,
            bot_handler,
            bot_general
        ],
        default_partial=bot_handler
    )

    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath=f"{args.persistence_dir}/prompetition_bot")
    application = (Application.builder()
                   .token(os.environ.get("TG_TOKEN"))
                   .persistence(persistence)
                   .build())

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", bot_general.start))
    application.add_handler(CommandHandler("help", bot_general.help_command))
    application.add_handler(CommandHandler("set_name", bot_general.set_name))

    application.add_handler(CommandHandler("switch", bot_handler.switch_debug_mode))
    application.add_handler(CommandHandler("submit", bot_handler.submit))

    application.add_handler(CommandHandler("task_show", bot_selector.show_task))
    application.add_handler(CommandHandler("task_list", bot_selector.task_list))
    application.add_handler(CommandHandler("task_select", bot_selector.select_task))

    application.add_handler(CommandHandler("snippet_list", bot_selector.snippet_list))
    application.add_handler(CommandHandler("snippet_focus", bot_selector.snippet_select))
    application.add_handler(CommandHandler("snippet_unfocus", bot_selector.snippet_unfocus))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_router.message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main(parse_args())
