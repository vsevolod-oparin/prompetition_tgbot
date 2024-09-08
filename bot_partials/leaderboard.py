from logging import Logger
from typing import List

from bot_partials.focus import FocusManagement
from bot_partials.partial import Partial
from telegram import Update
from telegram.ext import ContextTypes

from core.prompt_db import PromptDBManager, LeaderRow
from core.utils import from_txt_file, tg_user_id, html_escape

LEADERBOARD_SIZE = 10


class TGLeaderboard(Partial):

    def __init__(self, logger: Logger, sql_db: PromptDBManager):
        self.logger = logger
        self.sql_db = sql_db

    @staticmethod
    def form_board_lines(board: List[LeaderRow], user_id: str):
        idds = [
            idd for idd, row in enumerate(board)
            if row.user_id == user_id
        ]
        if len(idds) == 1:
            position = idds[0]
        else:
            position = None

        top_k = board[:LEADERBOARD_SIZE]
        top_k_lines = [
            f'{idd + 1}. {row.get_line(user_id)}'
            for idd, row in enumerate(top_k)
        ]
        if position is not None:
            if position > LEADERBOARD_SIZE:
                top_k_lines.append('...')
            if position >= LEADERBOARD_SIZE:
                top_k_lines.append(f'{position + 1}. {board[position].get_line(user_id)}')
        return  top_k_lines

    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get the leaderboard."""
        user = update.effective_user
        focus = FocusManagement(context)
        if focus.task is None:
            self.logger.info(f'/leaderboard / {user.id} / {user.name}: no task')
            await update.effective_chat.send_message('No task has been selected.')
            return

        board = self.sql_db.form_leader_board(focus.task)
        board = list(map(LeaderRow, board))

        user_id = tg_user_id(user.id)

        if len(board) == 0:
            self.logger.info(f'/leaderboard / {user.id} / {user.name} / {focus.task}: empty leaderboard')
            message = f'<b>Leaderboard {focus.task}</b>\n\nNo entries.'
            await update.effective_chat.send_message(message, parse_mode='HTML')
            return

        top_k_lines = TGLeaderboard.form_board_lines(board, user_id)

        self.logger.info(f'/leaderboard / {user.id} / {user.name} / {focus.task}: entries num {len(top_k_lines)}')
        top_k_msg = '\n'.join(top_k_lines)
        message = f'<b>Leaderboard {focus.task}</b>\n\n<code>{html_escape(top_k_msg)}</code>'

        await update.effective_chat.send_message(message, parse_mode='HTML')