# AI Intelligence Pipeline

An automated data collection, validation, enrichment, and integration pipeline for AI products, startup mentions, and research papers.

## Project Overview

The AI Intelligence Pipeline is designed to collect and process information from multiple AI-related sources. It validates incoming records, enriches research paper data with relevant GitHub repository information, and integrates datasets into a unified structure.

The project demonstrates an automated data engineering workflow using Python.

## Key Features

- Automated collection of AI product information.
- Startup mention data collection and processing.
- Research paper extraction from arXiv.
- GitHub repository matching and verification for research papers.
- Data validation and normalization.
- Integration of multiple datasets into a unified pipeline.
- Automated testing using pytest.
- Structured JSON-based data storage.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| Requests | API integration |
| BeautifulSoup | Web scraping |
| arXiv | Research paper collection |
| GitHub API | Repository matching |
| JSON | Data storage |
| Pytest | Automated testing |
| Git & GitHub | Version control |

## Project Structure

```text
AI-Intelligence-Pipeline/
│
├── src/
│   ├── master_pipeline.py
│   ├── research_scraper.py
│   ├── github_repository_matcher.py
│   └── github_quality_checker.py
│
├── data/
│
├── tests/
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/sanikagundakar9-alt/AI-Intelligence-Pipeline-project-.git
```

### 2. Navigate to Project Directory

```bash
cd AI-Intelligence-Pipeline-project-
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## Execution

Run the master pipeline:

```bash
python src/master_pipeline.py
```

Run individual modules:

```bash
python src/research_scraper.py
python src/github_repository_matcher.py
python src/github_quality_checker.py
```

## Dataset Summary

The integrated pipeline currently processes:

| Dataset | Records |
|---|---:|
| AI Products | 20 |
| Startup Mentions | 422 |
| Research Papers | 15 |
| **Total** | **457** |

## Automated Testing

The project includes automated tests using pytest.

Run tests:

```bash
pytest -v
```

## GitHub Repository

Source code and project documentation are maintained on GitHub:

[AI Intelligence Pipeline Repository](https://github.com/sanikagundakar9-alt/AI-Intelligence-Pipeline-project-)

## Security

- Environment variables are used for sensitive configuration.
- API tokens should be stored in a local `.env` file.
- The `.env` file must not be uploaded to GitHub.
- `.gitignore` is used to exclude sensitive and unnecessary files.

## Conclusion

The AI Intelligence Pipeline demonstrates an automated approach to collecting, validating, enriching, and integrating AI ecosystem data from multiple sources. It provides a structured foundation for building scalable AI intelligence and data engineering systems.