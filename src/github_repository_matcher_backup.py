
import os
import re
import json
import time
import base64
import requests

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(BASE_DIR, "research_papers_enriched.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "research_papers_matched.json")

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AI-Intelligence-Pipeline"
}

TOKEN = os.getenv("GITHUB_TOKEN")

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def normalize(text):
    text = (text or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def get_arxiv_id(paper):
    source_url = paper.get("source", {}).get("url", "")
    match = re.search(
        r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)",
        source_url
    )
    return match.group(1) if match else None


def search_repositories(title):
    params = {
        "q": f'"{title}" in:readme',
        "per_page": 10
    }

    try:
        response = requests.get(
            GITHUB_SEARCH_URL,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if response.status_code == 403:
            print("GitHub API rate limit reached.")
            return []

        response.raise_for_status()

        return response.json().get("items", [])

    except requests.RequestException as error:
        print("GitHub search error:", error)
        return []


def get_readme(full_name):
    url = f"https://api.github.com/repos/{full_name}/readme"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if response.status_code != 200:
            return ""

        data = response.json()

        if data.get("encoding") != "base64":
            return ""

        content = base64.b64decode(
            data["content"]
        ).decode("utf-8", errors="ignore")

        return content

    except (requests.RequestException, ValueError, KeyError) as error:
        print("README verification error:", error)
        return ""


def verify_repository(paper, repo):
    title = paper.get("content", {}).get("paperTitle", "")
    arxiv_id = get_arxiv_id(paper)

    readme = get_readme(repo["full_name"])

    if not readme:
        return False, "README_UNAVAILABLE"

    normalized_readme = normalize(readme)
    normalized_title = normalize(title)

    title_verified = (
        bool(normalized_title)
        and normalized_title in normalized_readme
    )

    arxiv_verified = (
        bool(arxiv_id)
        and arxiv_id.lower() in readme.lower()
    )

    if title_verified:
        return True, "EXACT_TITLE_IN_README"

    if arxiv_verified:
        return True, "ARXIV_ID_IN_README"

    return False, "NO_EXACT_EVIDENCE"


def search_repository(paper):
    content = paper.get("content", {})
    title = content.get("paperTitle", "")

    print("\nSearching:", title)

    candidates = search_repositories(title)

    for repo in candidates:
        time.sleep(1)

        verified, evidence = verify_repository(paper, repo)

        if verified:
            print("Verified repository:", repo["html_url"])

            return {
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "confidence": "HIGH",
                "evidence": evidence,
                "candidate_url": repo["html_url"]
            }

    print("No verified repository found.")

    return {
        "url": None,
        "stars": None,
        "confidence": "UNVERIFIED",
        "evidence": "NO_EXACT_EVIDENCE",
        "candidate_url": (
            candidates[0]["html_url"] if candidates else None
        )
    }


def main():
    if not os.path.exists(INPUT_FILE):
        print("Input file not found:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    print("Total papers:", len(papers))

    matched = 0
    searched = 0
    preserved = 0

    for paper in papers:
        content = paper.get("content", {})

        existing_url = (
            content.get("githubUrl")
            or content.get("github_url")
        )

        if existing_url:
            preserved += 1
            print("Existing URL preserved:", content.get("paperTitle"))
            continue

        result = search_repository(paper)
        searched += 1

        paper["githubMatch"] = result

        if result["url"]:
            content["githubUrl"] = result["url"]
            content["githubStars"] = result["stars"]
            matched += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n========== MATCHING SUMMARY ==========")
    print("Total papers:", len(papers))
    print("Papers searched:", searched)
    print("Existing URLs preserved:", preserved)
    print("New verified matches:", matched)
    print("Unverified papers:", searched - matched)
    print("Output saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
