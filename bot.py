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
import asyncio
import os
from pathlib import Path
from typing import List

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, PicklePersistence

from bot_partials.errors import TGErrorHandler
from bot_partials.general import TGBotGeneral
from bot_partials.leaderboard import TGLeaderboard
from bot_partials.logger import produce_logger, init_logging
from bot_partials.prompting import TGPrompter
from bot_partials.router import MessageRouter
from bot_partials.selector import TGSelector
from core.llm_manager import LLMManager
from core.prompt_db import PromptDBManager
from core.prompter import PromptRunner
from core.ratelimit import RateLimiter, RateLimitedBatchQueue
from core.task_management import TaskManager


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
    parser.add_argument(
        "--log_pth",
        type=str,
        default='logs',
        help="Path to log file"
    )
    return parser.parse_args(input_string)


def main(args) -> None:
    """Start the bot."""
    init_logging()

    aclient = AsyncOpenAI(
        api_key=os.environ['DS'],
        base_url='https://api.deepseek.com/beta'
    )

    task_manager = TaskManager(args)
    sql_db = PromptDBManager()
    llms = LLMManager(Path(args.data_root) / 'llm_config.yaml')

    limiter = RateLimiter()
    queue = RateLimitedBatchQueue(limiter)
    prompt_runner = PromptRunner(limiter, queue, sql_db, llms)

    logger = produce_logger(Path(args.log_pth) / 'bot.log', logger_tag='bot')
    prompt_logger = produce_logger(Path(args.log_pth) / 'prompts.log', logger_tag='prompts', propagate=False)
    error_logger = produce_logger(Path(args.log_pth) / 'error.log', logger_tag='error_bot')

    bot_general = TGBotGeneral(logger, sql_db)
    bot_leaderboard = TGLeaderboard(logger, sql_db)
    bot_prompter = TGPrompter(logger, prompt_logger, task_manager, prompt_runner)
    bot_selector = TGSelector(logger, task_manager)
    bot_error = TGErrorHandler(error_logger)

    bot_router = MessageRouter(
        partials=[
            bot_selector,
            bot_prompter,
            bot_general
        ],
        default_partial=bot_prompter
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
    application.add_handler(CommandHandler("whoami", bot_general.whoami))

    application.add_handler(CommandHandler("switch_debug_mode", bot_prompter.switch_debug_mode))
    application.add_handler(CommandHandler("switch_autoclean", bot_prompter.switch_autoclean))

    application.add_handler(CommandHandler("prompt_fetch", bot_prompter.prompt_fetch))

    application.add_handler(CommandHandler("run_snippet", bot_prompter.run_snippet))
    application.add_handler(CommandHandler("run_open", bot_prompter.run_open))
    application.add_handler(CommandHandler("run_to_score", bot_prompter.run_to_score))

    application.add_handler(CommandHandler("task_show", bot_selector.show_task))
    application.add_handler(CommandHandler("task_list", bot_selector.task_list))
    application.add_handler(CommandHandler("task_select", bot_selector.select_task))

    application.add_handler(CommandHandler("snippet_list", bot_selector.snippet_list))
    application.add_handler(CommandHandler("snippet_focus", bot_selector.snippet_select))
    application.add_handler(CommandHandler("snippet_unfocus", bot_selector.snippet_unfocus))

    application.add_handler(CommandHandler("leaderboard", bot_leaderboard.leaderboard))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_router.message))

    application.add_error_handler(bot_error.handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def to_close():
        await limiter.close()
        sql_db.close()
        await aclient.close()

    asyncio.run(to_close())


if __name__ == "__main__":
    main(parse_args())
