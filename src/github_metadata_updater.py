
import json
import os
import re
import requests

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

INPUT_FILE = BASE_DIR / "research_papers_enriched.json"
OUTPUT_FILE = BASE_DIR / "research_papers_final.json"

TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AI-Intelligence-Pipeline"
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_repository_details(url):

    if not url:
        return None

    match = re.search(
        r"github\.com/([^/]+)/([^/]+)",
        url
    )

    if not match:
        return None

    owner, repo = match.groups()
    repo = repo.removesuffix(".git")

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(
            api_url,
            headers=HEADERS,
            timeout=20
        )

        if response.status_code == 404:
            print(f"Repository not found: {owner}/{repo}")
            return None

        response.raise_for_status()

        data = response.json()

        return {
            "name": data["full_name"],
            "url": data["html_url"],
            "description": data.get("description"),
            "stars": data["stargazers_count"],
            "language": data.get("language"),
            "forks": data["forks_count"],
            "defaultBranch": data["default_branch"],
            "isArchived": data["archived"],
            "isFork": data["fork"]
        }

    except requests.RequestException as error:
        print(f"GitHub API error: {error}")
        return None


def main():

    if not INPUT_FILE.exists():
        print("Input file not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    found = 0

    for paper in papers:

        content = paper.get("content", {})
        url = content.get("githubUrl")

        if not url:
            content["githubMetadata"] = None
            continue

        print(f"\nChecking: {url}")

        details = get_repository_details(url)

        content["githubMetadata"] = details

        if details:
            found += 1
            print("Repository:", details["name"])
            print("Stars:", details["stars"])
            print("Language:", details["language"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nGitHub Metadata Update Completed!")
    print("--------------------------------")
    print("Total papers:", len(papers))
    print("Repositories verified:", found)
    print("Repositories missing:", len(papers) - found)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
