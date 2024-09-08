import unittest
from core.prompt_db import PromptDBManager


class TestPromptDBManager(unittest.TestCase):
    def setUp(self):
        self.db = PromptDBManager(':memory:')

    def tearDown(self):
        self.db.close()

    def test_insert_user(self):
        self.db.insert_user('user1', 'John Doe')
        users = self.db.get_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0][1], 'John Doe')

    def test_update_user_name(self):
        self.db.insert_user('user1', 'John Doe')
        self.db.update_user_name('user1', 'Vasya')
        users = self.db.get_users()
        self.assertEqual(users[0][1], 'Vasya')

    def test_insert_prompt_run(self):
        self.db.insert_user('user1', 'John Doe')
        self.db.insert_prompt_run('user1', 'task1', 'Sample prompt', 0.5, 10, 0.7, 5, {'param1': 'value1'})
        prompts = self.db.get_top_k_user_prompts('user1', 'task1', 1)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0][0], 'Sample prompt')

    def test_get_top_k_prompts(self):
        self.db.insert_user('user1', 'John Doe')
        self.db.insert_prompt_run('user1', 'task1', 'Sample prompt 1', 0.5, 10, 0.7, 5, {'param1': 'value1'})
        self.db.insert_prompt_run('user1', 'task1', 'Sample prompt 2', 0.6, 12, 0.8, 6, {'param1': 'value2'})
        prompts = self.db.get_top_k_prompts('task1', 2)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0][0], 'Sample prompt 1')
        self.assertEqual(prompts[1][0], 'Sample prompt 2')

    def test_get_top_k_user_prompts(self):
        self.db.insert_user('user1', 'John Doe')
        self.db.insert_prompt_run('user1', 'task1', 'Sample prompt 1', 0.5, 10, 0.7, 5, {'param1': 'value1'})
        self.db.insert_prompt_run('user2', 'task1', 'Sample prompt 2', 0.6, 12, 0.8, 6, {'param1': 'value2'})
        self.db.insert_prompt_run('user1', 'task1', 'Sample prompt 3', 0.6, 12, 0.8, 6, {'param1': 'value2'})
        prompts = self.db.get_top_k_user_prompts('user1', 'task1', 2)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0][0], 'Sample prompt 1')
        self.assertEqual(prompts[1][0], 'Sample prompt 3')

    def test_get_user_names_by_ids(self):
        self.db.insert_user('user1', 'John Doe')
        self.db.insert_user('user2', 'Masha')
        users = self.db.get_user_names_by_ids(['user1', 'user2'])
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0][1], 'John Doe')
        self.assertEqual(users[1][1], 'Masha')


if __name__ == "__main__":
    unittest.main()