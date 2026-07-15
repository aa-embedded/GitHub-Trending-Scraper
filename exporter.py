"""
exporter.py
===========

Handles exporting scraped repository data into CSV, Excel (.xlsx), and
JSON formats. Every export function is defensive: failures are logged
and re-raised as a single, clear ``ExportError`` so the caller can
handle them uniformly.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from config import CSV_OUTPUT_PATH, DATA_DIR, EXCEL_OUTPUT_PATH, JSON_OUTPUT_PATH

logger = logging.getLogger("github_trending_scraper")

# Column order used consistently across CSV and Excel exports.
EXPORT_COLUMNS: List[str] = [
    "rank",
    "name",
    "owner",
    "url",
    "description",
    "language",
    "stars",
    "forks",
    "today_stars",
]

# Human-readable column headers shown in the exported files.
COLUMN_HEADERS: Dict[str, str] = {
    "rank": "Rank",
    "name": "Repository Name",
    "owner": "Owner",
    "url": "Repository URL",
    "description": "Description",
    "language": "Language",
    "stars": "Stars",
    "forks": "Forks",
    "today_stars": "Stars Today",
}


class ExportError(Exception):
    """Raised when data cannot be exported to the requested file format."""


def _ensure_data_directory() -> None:
    """Ensure the ``data/`` output directory exists.

    Creates the directory (and any missing parents) if it does not
    already exist. Silently does nothing if it is already present.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _to_dataframe(repositories: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert the list of repository dictionaries into a pandas DataFrame.

    Args:
        repositories: The scraped repository records.

    Returns:
        pd.DataFrame: A DataFrame with columns ordered per
        ``EXPORT_COLUMNS`` and renamed to human-readable headers.
    """
    dataframe = pd.DataFrame(repositories, columns=EXPORT_COLUMNS)
    return dataframe.rename(columns=COLUMN_HEADERS)


def export_to_csv(repositories: List[Dict[str, Any]], path: Path = CSV_OUTPUT_PATH) -> Path:
    """Export repository data to a CSV file.

    Args:
        repositories: The scraped repository records.
        path: Destination path for the CSV file.

    Returns:
        Path: The path where the CSV file was written.

    Raises:
        ExportError: If the file cannot be written.
    """
    try:
        _ensure_data_directory()
        dataframe = _to_dataframe(repositories)
        dataframe.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info("CSV export completed: %s", path)
        return path
    except OSError as exc:
        logger.error("Failed to export CSV to %s: %s", path, exc)
        raise ExportError(f"Could not write CSV file to {path}: {exc}") from exc


def export_to_excel(repositories: List[Dict[str, Any]], path: Path = EXCEL_OUTPUT_PATH) -> Path:
    """Export repository data to an Excel (.xlsx) file.

    Uses ``openpyxl`` as the writer engine via pandas.

    Args:
        repositories: The scraped repository records.
        path: Destination path for the Excel file.

    Returns:
        Path: The path where the Excel file was written.

    Raises:
        ExportError: If the file cannot be written.
    """
    try:
        _ensure_data_directory()
        dataframe = _to_dataframe(repositories)
        dataframe.to_excel(path, index=False, engine="openpyxl", sheet_name="Trending")
        logger.info("Excel export completed: %s", path)
        return path
    except (OSError, ValueError) as exc:
        logger.error("Failed to export Excel to %s: %s", path, exc)
        raise ExportError(f"Could not write Excel file to {path}: {exc}") from exc


def export_to_json(repositories: List[Dict[str, Any]], path: Path = JSON_OUTPUT_PATH) -> Path:
    """Export repository data to a JSON file.

    Args:
        repositories: The scraped repository records.
        path: Destination path for the JSON file.

    Returns:
        Path: The path where the JSON file was written.

    Raises:
        ExportError: If the file cannot be written.
    """
    try:
        _ensure_data_directory()
        with path.open("w", encoding="utf-8") as json_file:
            json.dump(repositories, json_file, indent=4, ensure_ascii=False)
        logger.info("JSON export completed: %s", path)
        return path
    except (OSError, TypeError) as exc:
        logger.error("Failed to export JSON to %s: %s", path, exc)
        raise ExportError(f"Could not write JSON file to {path}: {exc}") from exc
