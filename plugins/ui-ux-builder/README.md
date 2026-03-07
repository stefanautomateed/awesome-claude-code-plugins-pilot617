# ui-ux-builder

Full-lifecycle UI/UX skill for Claude Code: requirements gathering, UX planning, user alignment, frontend implementation, and automated visual validation using Playwright screenshots.

## What it does

Guides you through a structured 6-phase workflow for building web UI:

1. **Gather Requirements** — captures purpose, pages, interactions, design constraints
2. **Create UX Plan** — structured plan with page inventory, component hierarchy, navigation flow
3. **Align with User** — section-by-section approval before implementation
4. **Implement** — build the frontend per the approved plan
5. **Validate with Playwright** — automated screenshots, page structure inspection, responsive checks
6. **Review with User** — present screenshots, iterate until approved

Also works standalone for quick screenshot/validation tasks without the full lifecycle.

## Prerequisites

- Python 3.10+
- Playwright with Chromium:
  ```bash
  pip install playwright && python -m playwright install chromium
  ```

## Installation

```bash
/plugin install ui-ux-builder@awesome-claude-code-plugins
```

## Usage

### Full lifecycle

Tell Claude Code to build a UI:

```
Build me a dashboard for tracking support tickets. Use Tailwind CSS with a dark theme.
```

The skill activates automatically and walks through all 6 phases.

### Standalone screenshots

```bash
# Full page screenshot
python screenshot.py http://localhost:3000 -o homepage.png

# Element screenshot
python screenshot.py http://localhost:3000 --selector ".hero" -o hero.png

# Mobile viewport
python screenshot.py http://localhost:3000 --width 375 --height 812 -o mobile.png

# Device emulation
python screenshot.py http://localhost:3000 --device "iPhone 13" -o iphone.png

# Wait for dynamic content
python screenshot.py http://localhost:3000 --wait-for ".chart svg" --wait 3 -o chart.png

# Batch routes from file
python screenshot.py http://localhost:3000 --routes routes.txt -o ./screenshots/

# Page structure as JSON
python screenshot.py http://localhost:3000 --structure
```

## How it works

The skill provides:

- **SKILL.md** — main instructions with the 6-phase workflow, command reference, and common mistakes
- **template.md** — UX plan template with structured sections for requirements, components, navigation, states, and responsive breakpoints
- **examples/sample.md** — completed example plan for a Support Dashboard app
- **scripts/screenshot.py** — Playwright CLI tool for screenshots, element capture, device emulation, batch routes, and page structure extraction
- **scripts/validate.sh** — setup validation script that checks Python, Playwright, Chromium, and screenshot functionality

All paths are resolved dynamically — no hardcoded absolute paths or user-specific references.
