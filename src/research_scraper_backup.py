
import os
import json
import re
import time
import requests
import feedparser

from difflib import SequenceMatcher
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# GitHub API token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# API URLs
ARXIV_API_URL = "https://export.arxiv.org/api/query"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Settings
MAX_RESULTS = 20

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "research_papers.json")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AI-Intelligence-Pipeline"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def get_github_repo(text):
    """Extract GitHub repository URL from text."""

    pattern = r"https?://github\.com/[\w.-]+/[\w.-]+"
    matches = re.findall(pattern, text)

    if matches:
        return matches[0].rstrip(".,)")

    return None


def get_github_stars(repo_url):
    """Fetch repository stars using GitHub API."""

    if not repo_url:
        return None

    match = re.search(
        r"github\.com/([\w.-]+)/([\w.-]+)",
        repo_url
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
            timeout=15
        )

        if response.status_code == 200:
            return response.json().get("stargazers_count")

        print(f"GitHub details unavailable: {owner}/{repo}")

    except requests.RequestException as error:
        print(f"GitHub API error: {error}")

    return None


def normalize_text(text):
    """Normalize text for repository matching."""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    stopwords = {
        "the", "a", "an", "of", "for", "and",
        "in", "on", "with", "to", "from", "using"
    }

    return {
        word for word in text.split()
        if len(word) > 2 and word not in stopwords
    }


def calculate_match_score(title, repo_name, description):
    """Calculate similarity between paper and repository."""

    title_tokens = normalize_text(title)

    combined_repo = f"{repo_name} {description or ''}"
    repo_tokens = normalize_text(combined_repo)

    if not title_tokens:
        return 0

    overlap = title_tokens.intersection(repo_tokens)

    token_score = len(overlap) / len(title_tokens)

    name_score = SequenceMatcher(
        None,
        title.lower(),
        repo_name.replace("-", " ").replace("_", " ").lower()
    ).ratio()

    return max(token_score, name_score)


def search_github_repository(title):
    """Search GitHub for a repository related to a research paper."""

    params = {
        "q": f'"{title}" in:name,description,readme',
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }

    try:
        response = requests.get(
            GITHUB_SEARCH_URL,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        repositories = response.json().get("items", [])

        best_repo = None
        best_score = 0

        for repo in repositories:

            score = calculate_match_score(
                title,
                repo.get("name", ""),
                repo.get("description", "")
            )

            if score > best_score:
                best_score = score
                best_repo = repo

        # Avoid attaching unrelated repositories
        if best_repo and best_score >= 0.50:

            print(
                f"GitHub match: {best_repo['full_name']} "
                f"(score: {best_score:.2f})"
            )

            return {
                "url": best_repo["html_url"],
                "stars": best_repo["stargazers_count"]
            }

        print(f"No reliable GitHub match: {title[:60]}")

    except requests.RequestException as error:
        print(f"GitHub search failed: {error}")

    return {
        "url": None,
        "stars": None
    }


def scrape_research_papers():

    print("Fetching AI research papers from arXiv...")

    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        "start": 0,
        "max_results": MAX_RESULTS,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    try:
        response = requests.get(
            ARXIV_API_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        papers = []

        for entry in feed.entries:

            title = " ".join(entry.title.split())
            abstract = " ".join(entry.summary.split())

            authors = [
                author.name
                for author in entry.authors
            ]

            paper_url = entry.link
            published_date = entry.published

            # First check the abstract for GitHub URL
            github_url = get_github_repo(
                title + " " + abstract
            )

            github_stars = None

            if github_url:
                github_stars = get_github_stars(github_url)

            else:
                # Search GitHub if URL is not found
                github_data = search_github_repository(title)

                github_url = github_data["url"]
                github_stars = github_data["stars"]

                # Avoid excessive GitHub API requests
                time.sleep(2)

            paper = {
                "schemaVersion": "1.0",
                "recordType": "RESEARCH_PAPER",
                "source": {
                    "name": "arXiv",
                    "url": paper_url
                },
                "content": {
                    "paperTitle": title,
                    "authors": authors,
                    "abstract": abstract,
                    "paperUrl": paper_url,
                    "githubUrl": github_url,
                    "githubStars": github_stars,
                    "publishedDate": published_date
                },
                "collectedAt": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            papers.append(paper)

            print(f"Collected: {title[:70]}")

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                papers,
                file,
                indent=4,
                ensure_ascii=False
            )

        print("\nResearch scraping completed!")
        print(f"Research papers collected: {len(papers)}")

        github_found = sum(
            1 for paper in papers
            if paper["content"]["githubUrl"]
        )

        print(f"GitHub repositories found: {github_found}")
        print(f"Saved to: {OUTPUT_FILE}")

        return papers

    except requests.RequestException as error:
        print(f"arXiv API error: {error}")
        return []


if __name__ == "__main__":
    scrape_research_papers()
