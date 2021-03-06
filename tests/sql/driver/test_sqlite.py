import os
import tempfile
import unittest

from galileodb.sql.driver.sqlite import SqliteAdapter
from tests.sql.adapter import AbstractTestSqlDatabase


class TestSqliteDatabase(AbstractTestSqlDatabase, unittest.TestCase):
    db_file = None

    def setUp(self) -> None:
        self.db_file = tempfile.mktemp('.sqlite', 'galileo_test_')
        super().setUp()

    def _create_sql_adapter(self):
        return SqliteAdapter(self.db_file)

    def tearDown(self) -> None:
        super().tearDown()
        os.remove(self.db_file)


if __name__ == '__main__':
    unittest.main()
