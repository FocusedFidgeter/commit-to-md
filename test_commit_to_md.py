import unittest
from unittest.mock import patch, AsyncMock, mock_open
import aiohttp
from commit_to_md import fetch_commits, fetch_diff, get_ai_notes, write_markdown


class TestCommitToMdBehavior(unittest.IsolatedAsyncioTestCase):

    @patch('aiohttp.ClientSession.get')
    @patch('builtins.open', new_callable=mock_open)
    async def test_fetch_latest_commit(self, mock_file, mock_get):
        # TODO: Implement the test
        pass


class TestCommitToMd(unittest.IsolatedAsyncioTestCase):

    @patch('aiohttp.ClientSession.get')
    async def test_fetch_commits(self, mock_get):
        # TODO: Implement the test
        pass

    @patch('aiohttp.ClientSession.get')
    async def test_fetch_diff(self, mock_get):
        # TODO: Implement the test
        pass

    @patch('openai.OpenAI.chat.Completion.create')
    async def test_get_ai_notes(self, mock_create):
        # TODO: Implement the test
        pass

    @patch('builtins.open', new_callable=mock_open)
    async def test_write_markdown(self, mock_file):
        # TODO: Implement the test
        pass


if __name__ == '__main__':
    unittest.main()