import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILES = {
    "PRODUCT": DATA_DIR / "products.json",
    "STARTUP_MENTION": DATA_DIR / "startups.json",
    "RESEARCH_PAPER": BASE_DIR / "research_papers_quality_checked.json"
}

OUTPUT_FILE = DATA_DIR / "ai_intelligence_graph.json"
SUMMARY_FILE = DATA_DIR / "pipeline_summary.json"


def load_dataset(name, path):
    if not path.exists():
        raise FileNotFoundError(f"{name} dataset not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(f"{name} dataset must contain a JSON list")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Invalid record in {name} at index {index}")

        required_fields = [
            "schemaVersion", "recordType", "source",
            "content", "collectedAt"
        ]

        missing = [field for field in required_fields if field not in record]

        if missing:
            raise ValueError(
                f"{name} record {index} missing fields: {missing}"
            )

        if record["recordType"] != name:
            raise ValueError(
                f"Unexpected recordType in {name}, index {index}"
            )

    print(f"{name}: {len(records)} records loaded and validated")
    return records


def main():
    print("\n===== AI INTELLIGENCE MASTER PIPELINE =====")

    all_records = []
    dataset_counts = {}
    warnings = []

    for name, path in INPUT_FILES.items():
        records = load_dataset(name, path)
        dataset_counts[name] = len(records)
        all_records.extend(records)

    record_types = Counter(
        record["recordType"] for record in all_records
    )

    github_quality = Counter(
        record.get("githubQuality", {}).get("quality", "MISSING")
        for record in all_records
        if record["recordType"] == "RESEARCH_PAPER"
    )

    startup_names = [
        record.get("content", {}).get("entityName")
        for record in all_records
        if record["recordType"] == "STARTUP_MENTION"
    ]

    duplicate_startups = len(startup_names) - len(set(startup_names))

    if duplicate_startups:
        warnings.append(
            f"{duplicate_startups} duplicate startup mentions detected"
        )

    unverified = github_quality.get("UNVERIFIED", 0)

    if unverified:
        warnings.append(
            f"{unverified} research papers have unverified GitHub matches"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(all_records, file, indent=4, ensure_ascii=False)

    summary = {
        "project": "AI Intelligence Pipeline",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalRecords": len(all_records),
        "datasetCounts": dataset_counts,
        "recordTypeDistribution": dict(record_types),
        "githubQualityDistribution": dict(github_quality),
        "duplicateStartupMentions": duplicate_startups,
        "warnings": warnings,
        "outputFile": str(OUTPUT_FILE.relative_to(BASE_DIR))
    }

    with open(SUMMARY_FILE, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    print("\n===== INTEGRATION SUMMARY =====")
    print("Total records:", len(all_records))
    print("Record types:", dict(record_types))
    print("GitHub quality:", dict(github_quality))
    print("Duplicate startup mentions:", duplicate_startups)

    print("\n===== OUTPUT FILES =====")
    print("Combined dataset:", OUTPUT_FILE)
    print("Summary report:", SUMMARY_FILE)
    print("\nMaster pipeline completed successfully!")


if __name__ == "__main__":
    main()
