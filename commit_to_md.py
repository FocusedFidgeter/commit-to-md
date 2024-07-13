import argparse
import aiohttp
import asyncio
import os
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
# Set your OpenAI API key, model, and prompts
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key)
MODEL = 'gpt-4o'
TEMPERATURE=0.0,
MAX_TOKENS=1024,
NOTES_PROMPT = """
# Principle Software Engineer

## IDENTITY and PURPOSE

You are a principle software engineer whose primary language is Python. Your primary responsibility is to read and take notes on git commits and diffs. You will meticulously analyze each commit and diff to identify key changes, improvements, and potential issues. You will then document your findings in a structured format that can be easily referenced by your team. You are adept at understanding and following formatting instructions, ensuring that your notes are always accurate and perfectly aligned with the intended outcome.

Take a step back and think step-by-step about how to achieve the best possible results by following the steps below.

## STEPS

1. The user will provide a markdown representation of the Commit changes including a unified diff.
2. Carefully read through the commit message to understand the purpose of the changes.
3. Analyze the diff to identify what files were changed, what lines were added or removed, and any other relevant modifications.
4. Take detailed notes on each commit, including:
	- A summary of the changes
	- Any potential issues or areas for further review
5. Organize your notes in a structured format that can be easily referenced by your team.

## OUTPUT INSTRUCTIONS

- Only output Markdown.
- All sections should be Heading level 3
- Subsections should be one Heading level higher than its parent section
- All bullet lists should have their own paragraph
- Ensure you follow ALL these instructions when creating your output.

"""
SEND_OFF_PROMPT = """
Think step by step. What is the purpose of this change? What are the key takeaways?
"""


# Set your API rate limit delay
RATE_LIMIT_DELAY = 5  # seconds
# CLI arguments / STRINGS
DESCRIPTION = """
This script fetches commit history from a GitHub repository and saves each commit as a separate Markdown file in a specified directory.
It uses the GitHub API to fetch the commit history, and the OpenAI API to generate notes based on the diff.
"""


def extract_patch(file):
    if 'patch' in file:
        patch_lines = file['patch'].split('\n')
        filtered_patch = '\n'.join(line for line in patch_lines if line.strip() != '\\ No newline at end of file')
        return filtered_patch
    return ""


async def fetch_commits(session, repo_url):
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        api_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        commits = []
        page = 1

        while True:
            async with session.get(api_url, params={'page': page, 'per_page': 100}) as response:
                response.raise_for_status()
                page_commits = await response.json()
                if not page_commits:
                    break
                commits.extend(page_commits)
                page += 1

        return commits
    except aiohttp.ClientError as e:
        print(f"Error fetching commits: {e}")
        raise


async def fetch_diff(session, repo_url, sha):
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        api_url = f'https://api.github.com/repos/{owner}/{repo}/commits/{sha}'
        async with session.get(api_url) as response:
            response.raise_for_status()
            commit_data = await response.json()
            return commit_data['files']
    except aiohttp.ClientError as e:
        print(f"Error fetching diff for commit {sha}: {e}")
        raise


async def get_ai_notes(diff):
    try:
        response = openai_client.chat.Completion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": f"{NOTES_PROMPT}\n\n{diff}"},
                {"role": "user", "content": f"{diff}\n{SEND_OFF_PROMPT}"},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        await asyncio.sleep(RATE_LIMIT_DELAY)
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error getting AI notes: {e}")
        return "Error getting AI notes."


async def write_markdown(commit, diff_files, output_dir, take_ai_notes=False):
    sha = commit['sha']
    message = commit['commit']['message']
    author = commit['commit']['author']['name']
    date = commit['commit']['author']['date']

    commit_str = f"# Message: {message}\n\n## Commit: {sha}\n\nAuthor: {author}\n\nDate: {date}\n\n"
    diff_header = f"### Diff\n\n```diff\n"
    diff_text = '\n'.join(extract_patch(file) for file in diff_files)
    diff_footer = "```\n\n"

    file_path = os.path.join(output_dir, f"{message.replace('.', '_')}.md")
    with open(file_path, 'w', encoding='utf-8') as f:

        f.write(commit_str)
        f.write(diff_header)
        f.write(diff_text)
        f.write(diff_footer)

    if take_ai_notes:
        with open(file_path, 'a', encoding='utf-8') as f:
            ai_notes = await get_ai_notes(diff_text)
            if ai_notes == "Error getting AI notes.":
                print(f"Error getting AI notes for commit {sha}: {ai_notes}")
            else:
                f.write("**Notes**:\n\n")
                f.write(ai_notes + '\n')


async def main():
    parser = argparse.ArgumentParser(description=str(DESCRIPTION))
    parser.add_argument('repo_url', help='The URL of the GitHub repository.')
    parser.add_argument('output_dir', help='The output directory for the Markdown files.')
    parser.add_argument(
        '--latest', 
        action='store_true', 
        help='Fetch only the latest commit.'
    )
    parser.add_argument(
        '--take-notes', 
        action='store_true', 
        help='Use the OpenAI API to take notes on the Commit changes.'
    )

    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    async with aiohttp.ClientSession() as session:
        try:
            commits = await fetch_commits(session, args.repo_url)
            if args.latest:
                commits = commits[:1]
            tasks = []
            for commit in commits:
                tasks.append(fetch_diff(session, args.repo_url, commit['sha']))

            diffs = await asyncio.gather(*tasks)
            for commit, diff_files in zip(commits, diffs):
                if args.take_notes:
                    await write_markdown(commit, diff_files, args.output_dir, take_ai_notes=True)
                else:
                    await write_markdown(commit, diff_files, args.output_dir)
            print(f"Commit history successfully written to {args.output_dir}/")

        except aiohttp.ClientError as e:
            print(f"Error fetching data from GitHub: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    asyncio.run(main())
