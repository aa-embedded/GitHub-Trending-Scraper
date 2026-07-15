"""
main.py
=======

Entry point for the GitHub Trending Scraper.

Orchestrates the full workflow:
    1. Parse command-line arguments (language filter, top-N limit).
    2. Fetch the GitHub trending page.
    3. Parse repository data from the HTML.
    4. Apply optional filtering/limiting.
    5. Export the results to CSV, Excel, and JSON.
    6. Print a professional colored summary to the console.

Usage:
    python main.py
    python main.py --language python
    python main.py --top 10
    python main.py --language javascript --top 5
"""

import argparse
import itertools
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init as colorama_init

from config import DEFAULT_LANGUAGE_FILTER
from exporter import ExportError, export_to_csv, export_to_excel, export_to_json
from scraper import (
    ScraperError,
    fetch_trending_page,
    filter_by_language,
    limit_results,
    parse_trending_repositories,
)
from utils import setup_logger

logger = setup_logger()


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the scraper.

    Args:
        argv: Optional list of argument strings (mainly for testing).
            When ``None``, arguments are read from ``sys.argv``.

    Returns:
        argparse.Namespace: Parsed arguments with ``language`` and ``top``
        attributes.
    """
    parser = argparse.ArgumentParser(
        prog="github-trending-scraper",
        description="Scrape trending GitHub repositories and export them to CSV/Excel/JSON.",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Filter repositories by programming language (e.g. python, javascript).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Export only the first N repositories.",
    )
    return parser.parse_args(argv)


class _Spinner:
    """A simple animated console spinner used as a progress indicator.

    Runs in a background thread so the main thread can perform network
    and parsing work while the spinner animates in place.
    """

    def __init__(self, message: str) -> None:
        """Initialize the spinner.

        Args:
            message: The text displayed next to the spinning cursor.
        """
        self._message = message
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _spin(self) -> None:
        """Animate the spinner until stopped (runs on a background thread)."""
        for frame in itertools.cycle(["|", "/", "-", "\\"]):
            if not self._running:
                break
            sys.stdout.write(f"\r{Fore.CYAN}{self._message} {frame}{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self) -> None:
        """Start the spinner animation in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear its line from the console."""
        self._running = False
        if self._thread is not None:
            self._thread.join()
        sys.stdout.write("\r" + " " * (len(self._message) + 4) + "\r")
        sys.stdout.flush()


def print_summary(
    repositories: List[Dict[str, Any]],
    language_filter: Optional[str],
    csv_path: str,
    excel_path: str,
    json_path: str,
    execution_time: float,
) -> None:
    """Print a professional, colored summary of the scraping run.

    Args:
        repositories: The final list of exported repository records.
        language_filter: The language filter applied, or ``None``.
        csv_path: Path to the exported CSV file.
        excel_path: Path to the exported Excel file.
        json_path: Path to the exported JSON file.
        execution_time: Total execution time in seconds.
    """
    separator = "-" * 51
    displayed_filter = language_filter if language_filter else DEFAULT_LANGUAGE_FILTER

    print(Fore.GREEN + separator + Style.RESET_ALL)
    print(Fore.GREEN + Style.BRIGHT + "GitHub Trending Scraper" + Style.RESET_ALL)
    print(Fore.GREEN + separator + Style.RESET_ALL)
    print(f"Repositories found: {Fore.CYAN}{len(repositories)}{Style.RESET_ALL}")
    print(f"Language filter: {Fore.CYAN}{displayed_filter}{Style.RESET_ALL}")
    print(f"Exported CSV: {Fore.YELLOW}{csv_path}{Style.RESET_ALL}")
    print(f"Exported Excel: {Fore.YELLOW}{excel_path}{Style.RESET_ALL}")
    print(f"Exported JSON: {Fore.YELLOW}{json_path}{Style.RESET_ALL}")
    print(f"Execution time: {Fore.CYAN}{execution_time:.2f} seconds{Style.RESET_ALL}")
    print(Fore.GREEN + separator + Style.RESET_ALL)


def run(argv: Optional[List[str]] = None) -> int:
    """Run the full scraping, filtering, and export workflow.

    Args:
        argv: Optional list of CLI argument strings (mainly for testing).

    Returns:
        int: Process exit code. ``0`` on success, ``1`` on failure.
    """
    colorama_init(autoreset=True)
    args = parse_arguments(argv)
    start_time = time.perf_counter()

    logger.info("Program started.")
    spinner = _Spinner("Fetching and parsing trending repositories")
    spinner.start()

    try:
        html = fetch_trending_page()
        repositories = parse_trending_repositories(html)
        repositories = filter_by_language(repositories, args.language)
        repositories = limit_results(repositories, args.top)

        spinner.stop()

        if not repositories:
            print(
                Fore.YELLOW
                + "No repositories matched the given criteria. Nothing to export."
                + Style.RESET_ALL
            )
            logger.warning("No repositories to export after filtering.")
            logger.info("Execution finished with no data.")
            return 0

        csv_path = export_to_csv(repositories)
        excel_path = export_to_excel(repositories)
        json_path = export_to_json(repositories)

        execution_time = time.perf_counter() - start_time
        print_summary(
            repositories=repositories,
            language_filter=args.language,
            csv_path=str(csv_path),
            excel_path=str(excel_path),
            json_path=str(json_path),
            execution_time=execution_time,
        )

        logger.info("Execution finished successfully in %.2f seconds.", execution_time)
        return 0

    except ScraperError as exc:
        spinner.stop()
        logger.error("Scraping failed: %s", exc)
        print(Fore.RED + Style.BRIGHT + f"Scraping error: {exc}" + Style.RESET_ALL)
        return 1

    except ExportError as exc:
        spinner.stop()
        logger.error("Export failed: %s", exc)
        print(Fore.RED + Style.BRIGHT + f"Export error: {exc}" + Style.RESET_ALL)
        return 1

    except Exception as exc:  # noqa: BLE001 - last-resort safety net
        spinner.stop()
        logger.exception("Unexpected error occurred: %s", exc)
        print(Fore.RED + Style.BRIGHT + f"Unexpected error: {exc}" + Style.RESET_ALL)
        return 1


if __name__ == "__main__":
    sys.exit(run())
