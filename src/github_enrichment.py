
import os
import json
import re
import time
import requests

from pathlib import Path
from dotenv import load_dotenv
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

INPUT_FILE = BASE_DIR / "research_papers_ai_only.json"
OUTPUT_FILE = BASE_DIR / "research_papers_enriched.json"

GITHUB_API = "https://api.github.com/search/repositories"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AI-Intelligence-Pipeline"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "in",
    "on", "with", "to", "from", "using", "based",
    "efficient", "scalable", "novel", "towards"
}


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return {
        word for word in text.split()
        if len(word) > 2 and word not in STOPWORDS
    }


def calculate_score(title, repo):

    title_words = normalize(title)

    repo_text = (
        repo.get("name", "") + " " +
        (repo.get("description") or "")
    )

    repo_words = normalize(repo_text)

    if not title_words:
        return 0, 0

    overlap = title_words.intersection(repo_words)

    token_score = len(overlap) / len(title_words)

    name_score = SequenceMatcher(
        None,
        title.lower(),
        repo.get("name", "").lower().replace("-", " ")
    ).ratio()

    score = max(token_score, name_score)

    return score, len(overlap)


def search_repository(title):

    words = sorted(normalize(title))

    if not words:
        return None

    # Search using important title keywords
    query = " ".join(words[:8])

    params = {
        "q": query + " in:name,description,readme",
        "sort": "stars",
        "order": "desc",
        "per_page": 30
    }

    try:
        response = requests.get(
            GITHUB_API,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if response.status_code == 403:
            print("GitHub API rate limit reached.")
            return None

        response.raise_for_status()

        repositories = response.json().get("items", [])

        best_repo = None
        best_score = 0
        best_overlap = 0

        for repo in repositories:

            score, overlap = calculate_score(title, repo)

            if score > best_score:
                best_score = score
                best_overlap = overlap
                best_repo = repo

        # Require reasonable similarity
        if best_repo and best_score >= 0.30 and best_overlap >= 2:

            print(
                f"Match: {best_repo['full_name']} "
                f"(score: {best_score:.2f})"
            )

            return {
                "url": best_repo["html_url"],
                "name": best_repo["full_name"],
                "description": best_repo.get("description"),
                "stars": best_repo["stargazers_count"],
                "matchScore": round(best_score, 2)
            }

        print(f"No reliable match: {title[:60]}")

    except requests.RequestException as error:
        print(f"GitHub search error: {error}")

    return None


def main():

    if not INPUT_FILE.exists():
        print("AI-only JSON file not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    found = 0

    for paper in papers:

        content = paper.get("content", {})

        # Preserve existing repository matches
        if content.get("githubUrl"):
            found += 1
            continue

        title = content.get("paperTitle", "Untitled")

        print(f"\nSearching: {title}")

        result = search_repository(title)

        if result:
            content["githubUrl"] = result["url"]
            content["githubStars"] = result["stars"]
            content["githubRepository"] = result["name"]
            content["githubDescription"] = result["description"]
            content["githubMatchScore"] = result["matchScore"]

            found += 1

        time.sleep(2)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(papers, file, indent=4, ensure_ascii=False)

    print("\nGitHub Enrichment Completed!")
    print("--------------------------------")
    print(f"Total AI papers: {len(papers)}")
    print(f"Repositories found: {found}")
    print(f"Repositories missing: {len(papers) - found}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
