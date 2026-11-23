
import json
from pathlib import Path

# Project folder path
BASE_DIR = Path(__file__).resolve().parent.parent

# Input and output files
INPUT_FILE = BASE_DIR / "research_papers_validated.json"
OUTPUT_FILE = BASE_DIR / "research_papers_ai_only.json"


def main():

    # Check whether input file exists
    if not INPUT_FILE.exists():
        print("Error: research_papers_validated.json not found!")
        return

    # Read validated research papers
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    # Check JSON structure
    if not isinstance(papers, list):
        print("Error: Expected a list of research papers.")
        return

    # Filter only AI-related papers
    ai_papers = [
        paper for paper in papers
        if paper.get("is_ai_related") is True
    ]

    # Save filtered papers into a new JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(ai_papers, file, indent=4, ensure_ascii=False)

    # Display results
    print("\nAI Relevance Filtering Completed!")
    print("---------------------------------")
    print(f"Total papers: {len(papers)}")
    print(f"AI-related papers saved: {len(ai_papers)}")
    print(f"Non-AI papers excluded: {len(papers) - len(ai_papers)}")
    print(f"Output saved to: {OUTPUT_FILE}")

    print("\nFiltered AI Research Papers:")

    for paper in ai_papers:
        content = paper.get("content", {})
        title = content.get("paperTitle", "Untitled")
        print("-", title)


if __name__ == "__main__":
    main()
