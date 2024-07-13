import unittest
from unittest.mock import patch, AsyncMock, mock_open
import aiohttp
from commit_to_md import fetch_commits, fetch_diff, get_ai_notes, write_markdown


class TestCommitToMdBehavior(unittest.IsolatedAsyncioTestCase):

    @patch('aiohttp.ClientSession.get')
    @patch('builtins.open', new_callable=mock_open)
    async def test_fetch_latest_commit(self, mock_file, mock_get):
        mock_response = AsyncMock()
        mock_response.json.return_value = [{"sha": "abc123"}]
        mock_get.return_value.__aenter__.return_value = mock_response

        repo_url = "https://api.github.com/repos/user/repo"
        async with aiohttp.ClientSession() as session:
            commits = await fetch_commits(session, repo_url)
        
        self.assertEqual(commits, [{"sha": "abc123"}])
        pass


class TestCommitToMd(unittest.IsolatedAsyncioTestCase):

    @patch('aiohttp.ClientSession.get')
    async def test_fetch_commits(self, mock_get):
        mock_response = AsyncMock()
        mock_response.json.return_value = [{"sha": "abc123"}]
        mock_get.return_value.__aenter__.return_value = mock_response

        repo_url = "https://api.github.com/repos/user/repo"
        async with aiohttp.ClientSession() as session:
            commits = await fetch_commits(session, repo_url)
        
        self.assertEqual(commits, [{"sha": "abc123"}])
        pass

    @patch('aiohttp.ClientSession.get')
    async def test_fetch_diff(self, mock_get):
        mock_response = AsyncMock()
        mock_response.text.return_value = "diff --git a/file.txt b/file.txt"
        mock_get.return_value.__aenter__.return_value = mock_response

        repo_url = "https://api.github.com/repos/user/repo"
        sha = "abc123"
        async with aiohttp.ClientSession() as session:
            diff = await fetch_diff(session, repo_url, sha)
        
        self.assertEqual(diff, "diff --git a/file.txt b/file.txt")
        pass

    @patch('openai.OpenAI.chat.Completion.create')
    async def test_get_ai_notes(self, mock_create):
        mock_create.return_value = AsyncMock()
        mock_create.return_value.choices = [{"message": {"content": "AI notes"}}]

        diff = "diff --git a/file.txt b/file.txt"
        notes = await get_ai_notes(diff)
        
        self.assertEqual(notes, "AI notes")
        pass

    @patch('builtins.open', new_callable=mock_open)
    async def test_write_markdown(self, mock_file):
        commit = {"sha": "abc123", "message": "Initial commit"}
        diff_files = ["file.txt"]
        output_dir = "output"
        mock_file().write = AsyncMock()

        await write_markdown(commit, diff_files, output_dir)
        
        mock_file().write.assert_called_once_with("# Commit abc123\n\nInitial commit\n\n## Files Changed\n\n- file.txt\n")
        pass


if __name__ == '__main__':
    unittest.main()
