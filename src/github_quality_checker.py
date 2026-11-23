
import json
import os
import re
import requests
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()

INPUT_FILE = "research_papers_final.json"
OUTPUT_FILE = "research_papers_quality_checked.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def normalize_text(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return set(text.split())


def calculate_relevance(paper_title, repo_name, description):
    paper_words = normalize_text(paper_title)
    repo_words = normalize_text(
        f"{repo_name or ''} {description or ''}"
    )

    if not paper_words or not repo_words:
        return 0.0

    overlap = len(paper_words & repo_words)
    score = overlap / len(paper_words)

    title_similarity = SequenceMatcher(
        None,
        paper_title.lower(),
        (repo_name or "").replace("-", " ").lower()
    ).ratio()

    return round((score * 0.7) + (title_similarity * 0.3), 2)


def fetch_repository(repo_url):
    if not repo_url:
        return None

    match = re.search(
        r"github\.com/([^/\s]+)/([^/\s?#]+)",
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
            timeout=20
        )

        if response.status_code != 200:
            print(f"Repository check failed: {repo_url} ({response.status_code})")
            return None

        return response.json()

    except requests.RequestException as error:
        print(f"GitHub API error: {error}")
        return None


def check_quality(paper, repository):
    if not repository:
        return {
            "quality": "UNVERIFIED",
            "relevanceScore": 0.0,
            "reason": "Repository could not be verified"
        }

    content = paper.get("content", {})

    title = (
        content.get("paperTitle")
        or content.get("title")
        or ""
    )

    repo_name = repository.get("name", "")
    description = repository.get("description") or ""

    score = calculate_relevance(
        title,
        repo_name,
        description
    )

    archived = repository.get("archived", False)
    is_fork = repository.get("fork", False)
    stars = repository.get("stargazers_count", 0)

    if archived:
        quality = "LOW"
        reason = "Repository is archived"

    elif score >= 0.50 and not is_fork:
        quality = "HIGH"
        reason = "Strong title/description match"

    elif score >= 0.25:
        quality = "MEDIUM"
        reason = "Partial title/description match"

    else:
        quality = "LOW"
        reason = "Weak title/description match"

    return {
        "quality": quality,
        "relevanceScore": score,
        "stars": stars,
        "forks": repository.get("forks_count", 0),
        "language": repository.get("language"),
        "archived": archived,
        "isFork": is_fork,
        "reason": reason
    }


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    print(f"Checking GitHub quality for {len(papers)} papers...\n")

    high = medium = low = unverified = 0

    for paper in papers:
        content = paper.get("content", {})
        github_url = (
            content.get("githubUrl")
            or content.get("github_url")
        )

        repository = fetch_repository(github_url)
        quality_result = check_quality(paper, repository)

        paper["githubQuality"] = quality_result

        quality = quality_result["quality"]

        if quality == "HIGH":
            high += 1
        elif quality == "MEDIUM":
            medium += 1
        elif quality == "LOW":
            low += 1
        else:
            unverified += 1

        title = (
            content.get("paperTitle")
            or content.get("title")
            or "Unknown title"
        )

        print(f"{title}")
        print(
            f"Quality: {quality} | "
            f"Score: {quality_result['relevanceScore']}"
        )
        print("-" * 60)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(papers, file, indent=4, ensure_ascii=False)

    print("\n========== QUALITY SUMMARY ==========")
    print(f"Total papers: {len(papers)}")
    print(f"HIGH quality: {high}")
    print(f"MEDIUM quality: {medium}")
    print(f"LOW quality: {low}")
    print(f"UNVERIFIED: {unverified}")
    print(f"\nSaved output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
