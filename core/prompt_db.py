import sqlite3
import json
from datetime import datetime
from typing import List, Any


import dataclasses

@dataclasses.dataclass
class LeaderRow:
    def __init__(self, tuple):
        self.run_id = tuple[0]
        self.user_id = tuple[1]
        self.user_name = tuple[2]
        self.task_id = tuple[3]
        self.prompt = tuple[4]
        self.hidden_value = tuple[5]
        self.open_value = tuple[6]
        if tuple[7]:
            self.parameters_json = json.loads(tuple[7])
        else:
            self.parameters_json = None
        self.creation_date = tuple[8]

    def get_line(self, user_id: str) -> str:
        prompt = self.prompt
        user_name = self.user_name
        if user_id and user_id == self.user_id:
            user_name = user_name + " (YOU)"
        return f'{self.hidden_value * 100:3.2f} - {user_name} - {len(prompt) = }'

class PromptDBManager:
    def __init__(self, db_name: str = 'persistence/sql.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                task_id TEXT,
                prompt_id INT,
                creation_date DATE,
                open_score REAL,
                open_runs INTEGER,
                hidden_score REAL,
                hidden_runs INTEGER,
                parameters_json TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                task_id TEXT,
                prompt TEXT
            )
        ''')
        self.conn.commit()

    def insert_prompt_run(self,
                      user_id: str,
                      task_id: str,
                      prompt_text: str,
                      open_score: float = 0.0,
                      open_runs: int = 0,
                      hidden_score: float = 0.0,
                      hidden_runs: int = 0,
                      parameters_json: Any = None):
        prompt_id = self.insert_prompt(
            user_id=user_id,
            task_id=task_id,
            prompt=prompt_text
        )
        parameters_dumped = json.dumps(parameters_json)

        self.cursor.execute('''
            SELECT run_id, open_score, open_runs, hidden_score, hidden_runs 
            FROM prompt_runs 
            WHERE user_id = ? AND task_id = ? AND prompt_id = ? AND parameters_json = ?
        ''', (user_id, task_id, prompt_id, parameters_dumped))
        existing_run = self.cursor.fetchone()
        if existing_run:
            run_id, prev_open_score, prev_open_runs, prev_hidden_score, prev_hidden_runs = existing_run
            self.cursor.execute('''
                UPDATE prompt_runs
                SET open_score = ?, open_runs = ?, hidden_score = ?, hidden_runs = ?
                WHERE run_id = ?
            ''', (
                prev_open_score + open_score,
                prev_open_runs + open_runs,
                prev_hidden_score + hidden_score,
                prev_hidden_runs + hidden_runs,
                run_id
            ))
        else:
            creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('''
                INSERT INTO prompt_runs (user_id, task_id, prompt_id, creation_date, open_score, open_runs, hidden_score, hidden_runs, parameters_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, task_id, prompt_id, creation_date, open_score, open_runs, hidden_score, hidden_runs, parameters_dumped))
        self.conn.commit()

    def insert_prompt(self, user_id: str, task_id: str, prompt: str) -> int:
        self.cursor.execute('''
            SELECT prompt_id 
            FROM prompts
            WHERE user_id = ? AND task_id = ? AND prompt = ?
        ''', (user_id, task_id, prompt))
        existing_prompt = self.cursor.fetchone()

        if existing_prompt:
            prompt_id = existing_prompt[0]
        else:
            self.cursor.execute('''
                INSERT INTO prompts (user_id, task_id, prompt)
                VALUES (?, ?, ?)
            ''', (user_id, task_id, prompt))
            prompt_id = self.cursor.lastrowid
            self.conn.commit()
        return prompt_id

    def insert_user(self, user_id: str, user_name: str):
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, user_name)
            VALUES (?, ?)
        ''', (user_id, user_name))
        self.conn.commit()

    def update_user_name(self, user_id, user_name):
        self.cursor.execute('''
            SELECT * 
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        existing_user = self.cursor.fetchone()

        if existing_user:
            self.cursor.execute('''
                UPDATE users
                SET user_name = ?
                WHERE user_id = ?
            ''', (user_name, user_id))
        else:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, user_name)
                VALUES (?, ?)
            ''', (user_id, user_name))
        self.conn.commit()

    def get_top_k_prompts(self, task_id: str, k: int):
        query = '''
            SELECT 
                p.prompt, pr.open_score, pr.open_runs, pr.hidden_score, pr.hidden_runs, pr.parameters_json
            FROM prompt_runs pr
            JOIN prompts p ON pr.prompt_id = p.prompt_id
            WHERE pr.task_id = ?
            ORDER BY CASE WHEN pr.hidden_runs > 0 THEN pr.hidden_score / pr.hidden_runs ELSE 0 END DESC
            LIMIT ?
        '''
        self.cursor.execute(query, (task_id, k))
        return self.cursor.fetchall()

    def form_leader_board(self, task_id: str):
        query = '''
            WITH CalculatedValues AS (
                SELECT
                    run_id,
                    user_id,
                    task_id,
                    prompt_id,
                    parameters_json,
                    creation_date,
                    CASE
                        WHEN hidden_runs > 0 THEN hidden_score / hidden_runs
                        ELSE 0
                    END AS hidden_value,
                    CASE
                        WHEN open_runs > 0 THEN open_score / open_runs
                        ELSE 0
                    END AS open_value
                FROM 
                    prompt_runs
                WHERE
                    task_id = ?
            ),
            SortedValues AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY user_id, task_id 
                        ORDER BY hidden_value DESC
                    ) AS rn
                FROM 
                    CalculatedValues
            )
            SELECT
                sv.run_id,
                sv.user_id,
                u.user_name,
                sv.task_id,
                p.prompt,
                sv.hidden_value,
                sv.open_value,
                sv.parameters_json,
                sv.creation_date
            FROM 
                SortedValues sv
            JOIN
                users u ON sv.user_id = u.user_id
            JOIN
                prompts p ON sv.prompt_id = p.prompt_id
            WHERE
                sv.rn = 1
            ORDER BY
                sv.hidden_value DESC, sv.creation_date ASC
        '''
        self.cursor.execute(query, (task_id,))
        return self.cursor.fetchall()

    def get_top_k_user_prompts(self, user_id, task_id, k):
        query = '''
            SELECT 
                p.prompt, pr.open_score, pr.open_runs, pr.hidden_score, pr.hidden_runs, pr.parameters_json
            FROM prompt_runs pr
            JOIN prompts p ON pr.prompt_id = p.prompt_id
            WHERE pr.task_id = ? AND pr.user_id = ?
            ORDER BY CASE WHEN pr.hidden_runs > 0 THEN pr.hidden_score / pr.hidden_runs ELSE 0 END DESC
            LIMIT ?
        '''
        self.cursor.execute(query, (task_id, user_id, k))
        return self.cursor.fetchall()

    def get_users(self):
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()

    def get_user_names_by_ids(self, user_ids: List[str]):
        placeholders = ', '.join('?' for _ in user_ids)
        query = f'''
            SELECT user_id, user_name 
            FROM users 
            WHERE user_id IN ({placeholders})
        '''
        self.cursor.execute(query, user_ids)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()