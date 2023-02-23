import os
import sys
import typing

parent_dir: str = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)

import unittest
import sqlite3

from unittest.mock import patch
from datetime import datetime, timedelta

from status_expiration_task import status_expiration
from database_interaction_functions import modulate_status, get_metadata_from_db, Metadata
from config import Configuration, generate_database_connection

class TestStatusThread(unittest.TestCase):
    def setUp(self) -> None:

        self.connection = sqlite3.connect(':memory:')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE savedState (
                user TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                expiration TEXT NOT NULL
            );
        ''')
        self.cursor.execute('''
            INSERT INTO savedState (user, status, expiration)
            VALUES ('testuser', 'busy', '2022-02-22 22:22:22');
        ''')
    def test_status_expiration_thread(self) -> None:
        test_config = Configuration.get_instance('test_config.ini')
        status_expiration(test_config)
        retrieved_metadata = get_metadata_from_db(self.connection, test_config)
        self.assertIsInstance(retrieved_metadata, Metadata)
        self.assertEqual(retrieved_metadata.status, 'avaliable')
    def tearDown(self) -> None:
        self.connection.close()
        
if __name__ == '__main__':
    unittest.main()
        
