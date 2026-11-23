
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "research_papers_validated.json"
OUTPUT_FILE = BASE_DIR / "research_papers_ai_only.json"


def main():

    if not INPUT_FILE.exists():
        print("Error: research_papers_validated.json not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    ai_papers = [
        paper for paper in papers
        if paper.get("is_ai_related") is True
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            ai_papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nFinal AI-only JSON Generated!")
    print("--------------------------------")
    print(f"Total papers: {len(papers)}")
    print(f"AI-related papers: {len(ai_papers)}")
    print(f"Excluded papers: {len(papers) - len(ai_papers)}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
