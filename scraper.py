"""
scraper.py
==========

Core scraping logic for the GitHub Trending Scraper.

Responsible for:
    * Sending HTTP requests to GitHub's trending page (with retries).
    * Parsing the returned HTML with BeautifulSoup.
    * Extracting and normalizing repository data into a list of
      dictionaries ready for export.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from config import (
    GITHUB_BASE_URL,
    GITHUB_TRENDING_URL,
    MAX_RETRIES,
    REPO_ARTICLE_SELECTOR,
    REPO_DESCRIPTION_SELECTOR,
    REPO_LANGUAGE_SELECTOR,
    REPO_STARS_FORKS_SELECTOR,
    REPO_TITLE_SELECTOR,
    REPO_TODAY_STARS_SELECTOR,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT_SECONDS,
    RETRY_BACKOFF_SECONDS,
    SUCCESS_STATUS_CODE,
)
from utils import build_repository_url, clean_text, parse_int, parse_today_stars

logger = logging.getLogger("github_trending_scraper")


class ScraperError(Exception):
    """Raised when the trending page cannot be fetched or parsed."""


def fetch_trending_page(url: str = GITHUB_TRENDING_URL) -> str:
    """Fetch the raw HTML of the GitHub trending page, with retries.

    Sends an HTTP GET request using the ``requests`` library. On
    connection errors or timeouts, the request is retried up to
    ``MAX_RETRIES`` times with an increasing backoff delay. Any
    non-200 response is treated as an invalid response.

    Args:
        url: The URL to fetch. Defaults to the GitHub trending page.

    Returns:
        str: The raw HTML content of the page.

    Raises:
        ScraperError: If the page cannot be retrieved after all retries,
            or if the server returns a non-success status code.
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Sending request to %s (attempt %d/%d)", url, attempt, MAX_RETRIES)
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            logger.info("Response received: HTTP %d", response.status_code)

            if response.status_code != SUCCESS_STATUS_CODE:
                raise ScraperError(
                    f"Invalid response from server: HTTP {response.status_code}"
                )

            return response.text

        except Timeout as exc:
            last_error = exc
            logger.warning("Request timed out on attempt %d: %s", attempt, exc)
        except RequestsConnectionError as exc:
            last_error = exc
            logger.warning("Connection error on attempt %d: %s", attempt, exc)
        except RequestException as exc:
            last_error = exc
            logger.warning("Request failed on attempt %d: %s", attempt, exc)

        if attempt < MAX_RETRIES:
            delay = RETRY_BACKOFF_SECONDS * attempt
            logger.info("Retrying in %.1f seconds...", delay)
            time.sleep(delay)

    logger.error("All %d request attempts failed.", MAX_RETRIES)
    raise ScraperError(f"Could not fetch {url} after {MAX_RETRIES} attempts: {last_error}")


def _extract_owner_and_name(article: Tag) -> tuple[str, str]:
    """Extract the repository owner and name from a trending article tag.

    Args:
        article: A BeautifulSoup ``Tag`` representing one repository row.

    Returns:
        tuple[str, str]: A ``(owner, name)`` pair. Both default to an
        empty string if the expected elements are missing.
    """
    title_tag = article.select_one(REPO_TITLE_SELECTOR)
    if title_tag is None:
        return "", ""

    link_tag = title_tag.select_one("a")
    if link_tag is None or not link_tag.get("href"):
        return "", ""

    href = clean_text(link_tag.get("href", ""))
    parts = [segment for segment in href.split("/") if segment]

    if len(parts) < 2:
        return "", ""

    owner, name = parts[0], parts[1]
    return owner, name


def _extract_stars_and_forks(article: Tag) -> tuple[int, int]:
    """Extract total stars and forks from a trending article tag.

    GitHub renders both values as sibling ``<a>`` tags matching the same
    CSS selector, where the first is stars and the second is forks.

    Args:
        article: A BeautifulSoup ``Tag`` representing one repository row.

    Returns:
        tuple[int, int]: A ``(stars, forks)`` pair, defaulting to
        ``(0, 0)`` when the elements cannot be found.
    """
    link_tags = article.select(REPO_STARS_FORKS_SELECTOR)

    stars = parse_int(link_tags[0].get_text()) if len(link_tags) > 0 else 0
    forks = parse_int(link_tags[1].get_text()) if len(link_tags) > 1 else 0

    return stars, forks


def _parse_repository(article: Tag, rank: int) -> Optional[Dict[str, Any]]:
    """Parse a single repository's data out of its article tag.

    Args:
        article: A BeautifulSoup ``Tag`` representing one repository row.
        rank: The repository's position on the trending page (1-indexed).

    Returns:
        Optional[Dict[str, Any]]: A dictionary with the repository's
        fields, or ``None`` if essential data (owner/name) is missing.
    """
    owner, name = _extract_owner_and_name(article)
    if not owner or not name:
        logger.warning("Skipping a repository at rank %d: missing owner/name.", rank)
        return None

    description_tag = article.select_one(REPO_DESCRIPTION_SELECTOR)
    description = clean_text(description_tag.get_text()) if description_tag else ""

    language_tag = article.select_one(REPO_LANGUAGE_SELECTOR)
    language = clean_text(language_tag.get_text()) if language_tag else "Unknown"

    stars, forks = _extract_stars_and_forks(article)

    today_stars_tag = article.select_one(REPO_TODAY_STARS_SELECTOR)
    today_stars = parse_today_stars(today_stars_tag.get_text()) if today_stars_tag else 0

    repository_url = build_repository_url(GITHUB_BASE_URL, f"{owner}/{name}")

    return {
        "rank": rank,
        "name": name,
        "owner": owner,
        "url": repository_url,
        "description": description,
        "language": language,
        "stars": stars,
        "forks": forks,
        "today_stars": today_stars,
    }


def parse_trending_repositories(html: str) -> List[Dict[str, Any]]:
    """Parse the GitHub trending page HTML into structured repository data.

    Args:
        html: The raw HTML content of the trending page.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, one per repository,
        each containing name, owner, URL, description, language, stars,
        forks, today's stars, and rank.

    Raises:
        ScraperError: If no repository elements can be found in the HTML,
            which usually indicates GitHub changed its page structure.
    """
    logger.info("Parsing started.")
    soup = BeautifulSoup(html, "lxml")
    articles = soup.select(REPO_ARTICLE_SELECTOR)

    if not articles:
        raise ScraperError(
            "No repository elements found on the page. "
            "GitHub may have changed its HTML structure."
        )

    repositories: List[Dict[str, Any]] = []
    for index, article in enumerate(articles, start=1):
        repository = _parse_repository(article, rank=index)
        if repository is not None:
            repositories.append(repository)

    logger.info("Repositories parsed: %d", len(repositories))
    return repositories


def filter_by_language(
    repositories: List[Dict[str, Any]], language: Optional[str]
) -> List[Dict[str, Any]]:
    """Filter repositories to only those matching a given language.

    The comparison is case-insensitive.

    Args:
        repositories: The full list of parsed repository dictionaries.
        language: The programming language to filter by, or ``None`` to
            skip filtering entirely.

    Returns:
        List[Dict[str, Any]]: The filtered list of repositories. If
        ``language`` is ``None`` or empty, the original list is returned
        unchanged.
    """
    if not language:
        return repositories

    normalized_target = language.strip().lower()
    return [
        repo for repo in repositories if repo["language"].strip().lower() == normalized_target
    ]


def limit_results(repositories: List[Dict[str, Any]], top: Optional[int]) -> List[Dict[str, Any]]:
    """Limit the repository list to the first ``top`` entries.

    Args:
        repositories: The list of repository dictionaries.
        top: The maximum number of repositories to keep, or ``None`` to
            keep all of them.

    Returns:
        List[Dict[str, Any]]: The truncated (or original) list.
    """
    if top is None or top <= 0:
        return repositories
    return repositories[:top]
