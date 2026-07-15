"""
utils.py
========

Shared helper utilities used across the scraper: logger setup, text
cleaning, and numeric normalization. Keeping these pure, well-tested
helpers separate from business logic keeps ``scraper.py`` and
``exporter.py`` focused on their own responsibilities.
"""

import logging
import re
from typing import Optional

from config import (
    LOG_DATE_FORMAT,
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOGGER_NAME,
    LOGS_DIR,
)


def setup_logger() -> logging.Logger:
    """Configure and return the project logger.

    Logs are written both to ``logs/scraper.log`` and to the console.
    Calling this function multiple times will not duplicate handlers.

    Returns:
        logging.Logger: A configured logger instance shared by all modules.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        # Logger already configured (e.g. imported twice); avoid duplicates.
        return logger

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def clean_text(raw_text: Optional[str]) -> str:
    """Clean and normalize raw text extracted from HTML.

    Strips leading/trailing whitespace and collapses internal whitespace
    (including newlines and tabs) into single spaces.

    Args:
        raw_text: The raw string extracted from a BeautifulSoup element,
            or ``None`` if the element was not found.

    Returns:
        str: A cleaned, single-line string. Returns an empty string if
        ``raw_text`` is ``None``.
    """
    if raw_text is None:
        return ""
    return re.sub(r"\s+", " ", raw_text).strip()


def parse_int(value: Optional[str]) -> int:
    """Convert a GitHub-formatted numeric string into an integer.

    Handles thousands separators (commas) and values such as ``"1,234"``
    or ``"12"``. Non-numeric or missing input safely returns ``0`` instead
    of raising an exception, keeping the scraper resilient to malformed
    or missing HTML content.

    Args:
        value: The raw numeric string (e.g. ``"1,234"``), or ``None``.

    Returns:
        int: The parsed integer, or ``0`` if parsing fails.
    """
    if not value:
        return 0

    cleaned = clean_text(value).replace(",", "")
    match = re.search(r"-?\d+", cleaned)
    if not match:
        return 0

    try:
        return int(match.group())
    except ValueError:
        return 0


def parse_today_stars(value: Optional[str]) -> int:
    """Extract the "stars today" count from its raw text form.

    GitHub renders this as something like ``"123 stars today"``. This
    function isolates the leading integer and safely defaults to ``0``
    when the text is missing or in an unexpected format.

    Args:
        value: The raw text (e.g. ``"123 stars today"``), or ``None``.

    Returns:
        int: The number of stars gained today, or ``0`` if unavailable.
    """
    if not value:
        return 0

    cleaned = clean_text(value).replace(",", "")
    match = re.search(r"\d+", cleaned)
    if not match:
        return 0

    try:
        return int(match.group())
    except ValueError:
        return 0


def build_repository_url(base_url: str, relative_path: str) -> str:
    """Join a base GitHub URL with a repository's relative path.

    Args:
        base_url: The GitHub root URL (e.g. ``"https://github.com"``).
        relative_path: The relative repository path (e.g. ``"/owner/repo"``).

    Returns:
        str: The fully-qualified repository URL.
    """
    return f"{base_url.rstrip('/')}/{relative_path.lstrip('/')}"
