
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "research_papers.json"
OUTPUT_FILE = BASE_DIR / "research_papers_validated.json"

# Strong AI/ML keywords
STRONG_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "neural networks",
    "transformer",
    "transformers",
    "large language model",
    "large language models",
    "llm",
    "llms",
    "reinforcement learning",
    "generative model",
    "generative models",
    "computer vision",
    "vision-language",
    "natural language processing",
    "federated learning",
    "xgboost",
    "adversarial learning",
    "diffusion model",
    "diffusion transformer",
    "hyperparameter optimization",
    "evolutionary algorithm",
    "evolutionary algorithms",
    "support vector machine",
    "random forest"
]

# Supporting keywords (not enough individually)
SUPPORTING_KEYWORDS = [
    "classification",
    "prediction",
    "predictive model",
    "embedding",
    "embeddings",
    "optimization",
    "regression",
    "feature extraction",
    "decision tree",
    "training data",
    "model training",
    "automated learning"
]


def validate_paper(paper):

    content = paper.get("content", {})

    title = content.get("paperTitle", "")
    abstract = content.get("abstract", "")

    text = (title + " " + abstract).lower()

    strong_matches = [
        keyword for keyword in STRONG_KEYWORDS
        if keyword in text
    ]

    supporting_matches = [
        keyword for keyword in SUPPORTING_KEYWORDS
        if keyword in text
    ]

    # Strong keyword OR at least two supporting keywords
    is_ai_related = (
        len(strong_matches) >= 1
        or len(supporting_matches) >= 2
    )

    matched_keywords = strong_matches + supporting_matches

    paper["is_ai_related"] = is_ai_related
    paper["matched_keywords"] = matched_keywords

    return paper


def main():

    if not INPUT_FILE.exists():
        print("Error: research_papers.json not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        papers = json.load(file)

    if not isinstance(papers, list):
        print("Error: Expected a list of research papers.")
        return

    validated_papers = [
        validate_paper(paper)
        for paper in papers
    ]

    ai_papers = [
        paper for paper in validated_papers
        if paper["is_ai_related"]
    ]

    non_ai_papers = len(validated_papers) - len(ai_papers)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            validated_papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nImproved AI Relevance Validation Completed!")
    print("-------------------------------------------")
    print(f"Total papers: {len(validated_papers)}")
    print(f"AI-related papers: {len(ai_papers)}")
    print(f"Non-AI papers: {non_ai_papers}")
    print(f"Output saved to: {OUTPUT_FILE}")

    print("\nAI-related papers:")

    for paper in ai_papers:
        content = paper.get("content", {})
        print("-", content.get("paperTitle", "Untitled"))
        print("  Matched:", ", ".join(paper["matched_keywords"]))


if __name__ == "__main__":
    main()
