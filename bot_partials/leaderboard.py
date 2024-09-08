from typing import List

from bot_partials.focus import FocusManagement
from bot_partials.partial import Partial
from bot_partials.state import MessageState
from telegram import Update
from telegram.ext import ContextTypes

from bot_partials.userdata_keys import USER_NAME_KEY, STATE_KEY
from core.prompt_db import PromptDBManager, LeaderRow
from core.utils import from_txt_file, tg_user_id, html_escape

LEADERBOARD_SIZE = 10


class TGLeaderboard(Partial):

    def __init__(self, sql_db: PromptDBManager):
        self.sql_db = sql_db

    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get the leaderboard."""
        focus = FocusManagement(context)
        board = self.sql_db.form_leader_board(focus.task)
        board = list(map(LeaderRow, board))
        user_id = tg_user_id(update.effective_user.id)

        if len(board) == 0:
            message = f'<b>Leaderboard {focus.task}</b>\n\nNo entries.'
            await update.effective_chat.send_message(message, parse_mode='HTML')
            return

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

        top_k_msg = '\n'.join(top_k_lines)
        message = f'<b>Leaderboard {focus.task}</b>\n\n<code>{html_escape(top_k_msg)}</code>'

        await update.effective_chat.send_message(message, parse_mode='HTML')