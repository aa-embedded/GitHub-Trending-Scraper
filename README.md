# GitHub Trending Scraper

a clean, well-structured scraper that collects real-time data from the
[GitHub Trending](https://github.com/trending) page and exports it into
**CSV**, **Excel (.xlsx)**, and **JSON** formats — built with clean,
modular architecture and full logging, error handling, and CLI support.

Built entirely with `requests` + `BeautifulSoup` (no Selenium, no headless
browser required).

---

## Features

- 🔍 Scrapes live data from `https://github.com/trending`
- 📦 Extracts for every repository:
  - Repository Name
  - Owner
  - Full Repository URL
  - Description
  - Programming Language
  - Total Stars
  - Total Forks
  - Stars Gained Today
  - Rank on the trending page
- 📤 Exports results to **CSV**, **Excel**, and **JSON** simultaneously
- 🔁 Automatic retry logic on connection errors / timeouts
- 🧹 Text cleaning and whitespace normalization
- 🔢 Automatic string-to-integer conversion for star/fork counts
- 🗂️ Clean, modular architecture (`scraper.py`, `exporter.py`, `config.py`, `utils.py`)
- 📝 Full logging to `logs/scraper.log` (start, requests, parsing, export, errors)
- 🎨 Colored console output via `colorama`
- ⏱️ Execution time tracking
- 🌀 Live progress indicator while fetching/parsing
- 🧵 Command-line arguments:
  - `--language` — filter results by programming language
  - `--top` — limit results to the first N repositories
- 🛡️ Robust error handling — the program never crashes unexpectedly

---

## Installation

1. Clone or download this repository.
2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Requirements

- Python 3.12+
- requests
- beautifulsoup4
- pandas
- openpyxl
- lxml
- colorama

All dependencies are pinned in [`requirements.txt`](requirements.txt).

---

## Project Structure

```
github-trending-scraper/
│
├── main.py              # Entry point: CLI, orchestration, console output
├── scraper.py            # HTTP requests, retries, HTML parsing
├── exporter.py            # CSV / Excel / JSON export logic
├── config.py               # Constants: URLs, paths, selectors, retry policy
├── utils.py                 # Logger setup, text cleaning, number parsing
├── requirements.txt
├── README.md
├── LICENSE
│
├── data/                 # Exported output files
│   ├── trending.csv
│   ├── trending.xlsx
│   └── trending.json
│
├── logs/                 # Execution logs
│   └── scraper.log
│
└── screenshots/          # Console/output screenshots for documentation
```

---

## Screenshots

> Add screenshots of the console output and exported files here once
> available (e.g. `screenshots/console_output.png`,
> `screenshots/excel_output.png`).

| Console Output | Excel Output |
|---|---|
| _screenshot placeholder_ | _screenshot placeholder_ |

---

## Usage

Run the scraper with default settings (scrapes all trending repositories
for today):

```bash
python main.py
```

### Filter by programming language

```bash
python main.py --language python
```

### Limit to the top N repositories

```bash
python main.py --top 10
```

### Combine both options

```bash
python main.py --language javascript --top 5
```

---

## Sample Output

Console summary:

```
---------------------------------------------------
GitHub Trending Scraper
---------------------------------------------------
Repositories found: 25
Language filter: None
Exported CSV: data/trending.csv
Exported Excel: data/trending.xlsx
Exported JSON: data/trending.json
Execution time: 1.42 seconds
---------------------------------------------------
```

Sample JSON record:

```json
{
    "rank": 1,
    "name": "awesome-llm-apps",
    "owner": "Shubhamsaboo",
    "url": "https://github.com/Shubhamsaboo/awesome-llm-apps",
    "description": "100+ AI Agent & RAG apps you can actually run.",
    "language": "Python",
    "stars": 120443,
    "forks": 17842,
    "today_stars": 1104
}
```

---

## Technologies Used

| Technology | Purpose |
|---|---|
| `requests` | HTTP requests with retry handling |
| `BeautifulSoup4` + `lxml` | HTML parsing |
| `pandas` | Data structuring and CSV/Excel export |
| `openpyxl` | Excel (.xlsx) file writing engine |
| `colorama` | Cross-platform colored console output |
| `logging` | Structured, timestamped logging to file |
| `argparse` | Command-line interface |
| `pathlib` | Cross-platform, object-oriented file paths |

---

## Future Improvements

- Add support for scraping trending repositories by date range (daily/weekly/monthly)
- Add pagination support for "trending developers" alongside repositories
- Add a `--output-dir` CLI flag to customize the export destination
- Add unit tests with `pytest` and HTML fixtures for parser regression testing
- Add a Dockerfile for containerized execution
- Add a scheduled/cron mode for periodic scraping and historical trend tracking
- Add a simple web dashboard (Flask/FastAPI) to visualize trending data over time

---

## License

This project is licensed under the [MIT License](LICENSE).
