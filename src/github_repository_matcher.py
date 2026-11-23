
import os
import re
import json
import time
import base64
import requests

from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(BASE_DIR, "research_papers_enriched.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "research_papers_matched.json")

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AI-Intelligence-Pipeline"
}

TOKEN = os.getenv("GITHUB_TOKEN")

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this",
    "using", "based", "into", "through", "without",
    "their", "which", "learned", "learning", "towards",
    "approach", "method", "methods", "study", "paper",
    "analysis", "new", "efficient", "scalable"
}

TRACKER_TERMS = {
    "paper tracker",
    "arxiv tracker",
    "research paper tracker",
    "daily papers",
    "paper collection",
    "awesome papers",
    "research papers list"
}

CODE_EXTENSIONS = (
    ".py", ".ipynb", ".js", ".ts", ".java", ".cpp",
    ".c", ".go", ".rs", ".r", ".jl", ".m",
    ".sh", ".yaml", ".yml", ".sql"
)

IMPLEMENTATION_NAMES = {
    "src", "source", "code", "model", "models",
    "implementation", "experiments", "notebooks",
    "scripts", "train", "training", "inference"
}


def normalize(text):
    text = (text or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def get_keywords(text):
    words = normalize(text).split()

    return {
        word for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


def get_arxiv_id(paper):
    url = paper.get("source", {}).get("url", "")

    match = re.search(
        r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?",
        url
    )

    return match.group(1) if match else None


def api_get(url, params=None):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if response.status_code == 403:
            print("GitHub API rate limit reached.")
            return None

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        print("GitHub API error:", error)
        return None


def get_readme(full_name):
    data = api_get(
        f"{GITHUB_API}/repos/{full_name}/readme"
    )

    if not data:
        return ""

    try:
        if data.get("encoding") != "base64":
            return ""

        return base64.b64decode(
            data["content"]
        ).decode("utf-8", errors="ignore")

    except (ValueError, KeyError):
        return ""


def get_repository(full_name):
    return api_get(
        f"{GITHUB_API}/repos/{full_name}"
    )


def get_repository_files(full_name, default_branch):
    url = (
        f"{GITHUB_API}/repos/{full_name}/git/trees/"
        f"{default_branch}"
    )

    data = api_get(url, {"recursive": "1"})

    if not data:
        return []

    return [
        item["path"]
        for item in data.get("tree", [])
        if item.get("type") == "blob"
    ]


def extract_repo_name(url):
    if not url:
        return None

    parsed = urlparse(url)

    if parsed.netloc.lower() not in (
        "github.com",
        "www.github.com"
    ):
        return None

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        return None

    if parts[0] in ("", "settings"):
        return None

    return f"{parts[0]}/{parts[1].removesuffix('.git')}"


def is_tracker_repository(repo, readme):
    name = normalize(repo.get("name", ""))
    description = normalize(repo.get("description", ""))
    readme_text = normalize(readme[:5000])

    combined = name + " " + description + " " + readme_text

    if any(term in combined for term in TRACKER_TERMS):
        return True

    if "tracker" in name or "paper radar" in name:
        return True

    return False


def analyze_repository(paper, full_name):
    content = paper.get("content", {})

    title = content.get("paperTitle", "")
    abstract = content.get("abstract", "")
    arxiv_id = get_arxiv_id(paper)

    repo = get_repository(full_name)

    if not repo:
        return {
            "status": "REVIEW_REQUIRED",
            "evidence": "REPOSITORY_UNAVAILABLE",
            "repo": None
        }

    readme = get_readme(full_name)

    if not readme:
        return {
            "status": "REVIEW_REQUIRED",
            "evidence": "README_UNAVAILABLE",
            "repo": repo
        }

    if is_tracker_repository(repo, readme):
        return {
            "status": "REJECTED",
            "evidence": "PAPER_TRACKER_OR_AGGREGATOR",
            "repo": repo
        }

    branch = repo.get("default_branch", "main")

    files = get_repository_files(full_name, branch)

    if not files:
        return {
            "status": "REVIEW_REQUIRED",
            "evidence": "REPOSITORY_FILES_UNAVAILABLE",
            "repo": repo
        }

    code_files = [
        path for path in files
        if path.lower().endswith(CODE_EXTENSIONS)
    ]

    implementation_files = [
        path for path in code_files
        if any(
            folder in path.lower().split("/")
            for folder in IMPLEMENTATION_NAMES
        )
    ]

    if not code_files:
        return {
            "status": "REVIEW_REQUIRED",
            "evidence": "NO_CODE_FILES_FOUND",
            "repo": repo
        }

    repo_text = normalize(
        repo.get("name", "") + " " +
        repo.get("description", "") + " " +
        readme + " " +
        " ".join(files[:300])
    )

    title_keywords = get_keywords(title)
    repo_keywords = get_keywords(repo_text)

    if title_keywords:
        overlap = title_keywords.intersection(repo_keywords)
        relevance = len(overlap) / len(title_keywords)
    else:
        relevance = 0

    normalized_readme = normalize(readme)
    normalized_title = normalize(title)

    exact_title = (
        bool(normalized_title)
        and normalized_title in normalized_readme
    )

    arxiv_mentioned = (
        bool(arxiv_id)
        and arxiv_id in readme
    )

    # An arXiv ID alone is never implementation evidence.
    if arxiv_mentioned and not exact_title:
        return {
            "status": "MENTION_ONLY",
            "evidence": "ARXIV_ID_ONLY_IN_README",
            "repo": repo,
            "relevance": round(relevance, 2)
        }

    # Require strong paper relevance and actual code.
    if relevance >= 0.65 and (
        exact_title or len(implementation_files) > 0
    ):
        return {
            "status": "VERIFIED_IMPLEMENTATION",
            "evidence": "TOPIC_RELEVANCE_AND_CODE_FILES",
            "repo": repo,
            "relevance": round(relevance, 2),
            "code_file_count": len(code_files),
            "implementation_file_count": len(implementation_files)
        }

    return {
        "status": "REVIEW_REQUIRED",
        "evidence": "INSUFFICIENT_IMPLEMENTATION_EVIDENCE",
        "repo": repo,
        "relevance": round(relevance, 2),
        "code_file_count": len(code_files),
        "implementation_file_count": len(implementation_files)
    }


def search_repositories(paper):
    content = paper.get("content", {})

    title = content.get("paperTitle", "")
    arxiv_id = get_arxiv_id(paper)

    queries = []

    if title:
        queries.append(f'"{title}"')

    if arxiv_id:
        queries.append(arxiv_id)

    candidates = []
    seen = set()

    for query in queries:
        print("GitHub search:", query)

        data = api_get(
            f"{GITHUB_API}/search/repositories",
            {
                "q": query,
                "per_page": 10,
                "sort": "best-match"
            }
        )

        if not data:
            continue

        for repo in data.get("items", []):
            name = repo.get("full_name")

            if name and name not in seen:
                candidates.append(name)
                seen.add(name)

        time.sleep(1)

    return candidates


def search_repository(paper, used_repositories):
    content = paper.get("content", {})
    title = content.get("paperTitle", "")

    print("\nSearching:", title)

    existing_url = (
        content.get("githubUrl")
        or content.get("github_url")
    )

    existing_repo = extract_repo_name(existing_url)

    candidates = []

    if existing_repo:
        candidates.append(existing_repo)

    for name in search_repositories(paper):
        if name not in candidates:
            candidates.append(name)

    review_candidate = None

    for full_name in candidates:
        print("Checking:", full_name)

        if full_name in used_repositories:
            print("Skipped: repository already assigned to another paper")
            continue

        result = analyze_repository(paper, full_name)

        status = result["status"]
        repo = result.get("repo")

        print("Result:", status, result["evidence"])

        if status == "VERIFIED_IMPLEMENTATION" and repo:
            used_repositories.add(full_name)

            return {
                "url": repo.get("html_url"),
                "stars": repo.get("stargazers_count"),
                "confidence": "HIGH",
                "status": status,
                "evidence": result["evidence"],
                "relevance": result.get("relevance"),
                "candidate_url": repo.get("html_url")
            }

        if status in ("REVIEW_REQUIRED", "MENTION_ONLY") and repo:
            if review_candidate is None:
                review_candidate = {
                    "url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count"),
                    "evidence": result["evidence"],
                    "relevance": result.get("relevance")
                }

        time.sleep(1)

    if review_candidate:
        return {
            "url": None,
            "stars": None,
            "confidence": "LOW",
            "status": "REVIEW_REQUIRED",
            "evidence": review_candidate["evidence"],
            "relevance": review_candidate.get("relevance"),
            "candidate_url": review_candidate["url"]
        }

    return {
        "url": None,
        "stars": None,
        "confidence": "UNVERIFIED",
        "status": "NOT_FOUND",
        "evidence": "NO_VALID_IMPLEMENTATION_FOUND",
        "candidate_url": None
    }


def main():
    if not os.path.exists(INPUT_FILE):
        print("Input file not found:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    print("Total papers:", len(papers))

    verified = 0
    review = 0
    not_found = 0

    used_repositories = set()

    for paper in papers:
        content = paper.get("content", {})

        result = search_repository(
            paper,
            used_repositories
        )

        paper["githubMatch"] = result

        # Only strong implementation matches enter githubUrl.
        content["githubUrl"] = result["url"]
        content["githubStars"] = result["stars"]

        if result["status"] == "VERIFIED_IMPLEMENTATION":
            verified += 1
        elif result["status"] == "REVIEW_REQUIRED":
            review += 1
        else:
            not_found += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n========== MATCHING SUMMARY ==========")
    print("Total papers:", len(papers))
    print("Verified implementations:", verified)
    print("Review required:", review)
    print("Not found / mention only:", not_found)
    print("Output saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
