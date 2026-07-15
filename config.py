"""
config.py
=========

Centralized configuration for the GitHub Trending Scraper.

This module holds every constant used across the project: URLs, HTTP
settings, retry policy, file paths, and logging configuration. Keeping
these values in one place avoids magic numbers/strings scattered through
the codebase and makes the project easy to tune or extend.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Project paths
# --------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
LOGS_DIR: Path = BASE_DIR / "logs"
SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"

CSV_OUTPUT_PATH: Path = DATA_DIR / "trending.csv"
EXCEL_OUTPUT_PATH: Path = DATA_DIR / "trending.xlsx"
JSON_OUTPUT_PATH: Path = DATA_DIR / "trending.json"
LOG_FILE_PATH: Path = LOGS_DIR / "scraper.log"

# --------------------------------------------------------------------------
# Target website
# --------------------------------------------------------------------------
GITHUB_TRENDING_URL: str = "https://github.com/trending"

# A realistic desktop User-Agent reduces the chance of being blocked and
# mimics a normal browser request.
REQUEST_HEADERS: dict = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# --------------------------------------------------------------------------
# HTTP / retry behaviour
# --------------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS: int = 10
MAX_RETRIES: int = 3
RETRY_BACKOFF_SECONDS: float = 1.5
SUCCESS_STATUS_CODE: int = 200

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
LOGGER_NAME: str = "github_trending_scraper"

# --------------------------------------------------------------------------
# HTML parsing selectors
# --------------------------------------------------------------------------
REPO_ARTICLE_SELECTOR: str = "article.Box-row"
REPO_TITLE_SELECTOR: str = "h2.h3"
REPO_DESCRIPTION_SELECTOR: str = "p.col-9"
REPO_LANGUAGE_SELECTOR: str = 'span[itemprop="programmingLanguage"]'
REPO_STARS_FORKS_SELECTOR: str = "a.Link--muted.d-inline-block"
REPO_TODAY_STARS_SELECTOR: str = "span.d-inline-block.float-sm-right"

# --------------------------------------------------------------------------
# Misc defaults
# --------------------------------------------------------------------------
DEFAULT_LANGUAGE_FILTER: str = "None"
GITHUB_BASE_URL: str = "https://github.com"
