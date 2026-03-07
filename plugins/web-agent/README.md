# web-agent — Web Automation Agent

General-purpose web automation agent for Claude Code. Navigate websites, interact with UI elements, fill forms, extract data, and handle logins — all powered by Playwright.

## Quick Start

```shell
/plugin install web-agent@awesome-claude-code-plugins
```

Then use it:

```
/web-agent "Go to github.com/anthropics/claude-code and extract the star count"
```

## Prerequisites

- Python 3.9+
- Playwright + Chromium:
  ```bash
  pip install playwright && python -m playwright install chromium
  ```

## Usage

```
/web-agent <task description>
/web-agent --headed <task description>
```

### Examples

```
/web-agent "Go to news.ycombinator.com and get the top 5 story titles"
/web-agent "Go to npmjs.com, search for 'playwright', and extract the weekly downloads"
/web-agent --headed "Go to my-app.localhost:3000, log in, and check the dashboard"
```

## What It Can Do

- **Navigate** — Go to any URL, follow links, handle redirects
- **Interact** — Click buttons, fill forms, select dropdowns, press keys
- **Extract** — Pull text, tables, links, and structured data from pages
- **Authenticate** — Detect login pages and fill credentials (asks you interactively)
- **Screenshot** — Capture pages at any step for visual verification
- **Dynamic content** — Wait for SPAs, async-loaded content, and JS-rendered pages

## How It Works

The plugin includes:

1. **A skill** (`/web-agent`) — entry point that accepts your task description
2. **A subagent** — specialized web automation agent that runs in its own context
3. **A Playwright runner** (`run_browser.py`) — core Python library with `BrowserSession` class

The subagent generates and runs Playwright scripts in a loop:
- Navigate to the target URL
- Analyze the page (interactive elements, text content, screenshots)
- Perform actions (click, type, select)
- Verify results via screenshots
- Iterate until the task is complete

## CLI Usage (Standalone)

The runner can also be used directly:

```bash
# Navigate and get page info as JSON
python scripts/run_browser.py navigate https://example.com

# Take a screenshot
python scripts/run_browser.py screenshot https://example.com -o page.png

# List all interactive elements
python scripts/run_browser.py elements https://example.com

# Extract text
python scripts/run_browser.py extract https://example.com --selector "h1"

# Get page DOM structure
python scripts/run_browser.py structure https://example.com

# Add --headed to any command to see the browser
python scripts/run_browser.py --headed navigate https://example.com
```

## Architecture

```
plugins/web-agent/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── agents/
│   └── web-agent.md         # Subagent system prompt
├── skills/
│   └── web-agent/
│       └── SKILL.md         # /web-agent skill entry point
├── scripts/
│   ├── run_browser.py       # Core BrowserSession class
│   ├── requirements.txt     # Python dependencies
│   └── actions/
│       ├── navigate.py      # Navigation helpers
│       ├── interact.py      # Click/type/select helpers
│       ├── extract.py       # Data extraction helpers
│       └── auth.py          # Login detection + form filling
└── README.md
```

## License

[MIT](../../LICENSE)
