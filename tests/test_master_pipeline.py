import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MASTER_FILE = DATA_DIR / "ai_intelligence_graph.json"
SUMMARY_FILE = DATA_DIR / "pipeline_summary.json"


def test_master_dataset_exists():
    assert MASTER_FILE.exists()


def test_summary_file_exists():
    assert SUMMARY_FILE.exists()


def test_master_dataset_is_valid_json():
    with open(MASTER_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    assert data is not None


def test_summary_is_valid_json():
    with open(SUMMARY_FILE, "r", encoding="utf-8") as file:
        summary = json.load(file)

    assert isinstance(summary, dict)


def test_master_dataset_has_records():
    with open(MASTER_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    assert len(data) > 0


def test_summary_has_content():
    with open(SUMMARY_FILE, "r", encoding="utf-8") as file:
        summary = json.load(file)

    assert len(summary) > 0