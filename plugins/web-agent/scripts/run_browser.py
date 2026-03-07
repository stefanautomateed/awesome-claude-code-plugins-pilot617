#!/usr/bin/env python3
"""Core browser automation runner using Playwright.

Provides BrowserSession — a high-level wrapper around Playwright's Chromium
browser that supports navigation, clicking, typing, screenshots, element
discovery, and text extraction.

Usage as a library:
    from run_browser import BrowserSession
    with BrowserSession() as browser:
        result = browser.navigate("https://example.com")
        print(result)

Usage from CLI:
    python run_browser.py navigate https://example.com
    python run_browser.py screenshot https://example.com -o page.png
    python run_browser.py elements https://example.com
    python run_browser.py extract https://example.com --selector "h1"
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


@dataclass
class PageResult:
    """Result returned after each browser action."""

    url: str = ""
    title: str = ""
    screenshot_path: str = ""
    interactive_elements: list = field(default_factory=list)
    page_text: str = ""
    console_errors: list = field(default_factory=list)
    success: bool = True
    error: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class BrowserSession:
    """High-level Playwright browser wrapper.

    Parameters
    ----------
    headed : bool
        If True, launches a visible browser window. Default False (headless).
    screenshot_dir : str | None
        Directory for saving screenshots. Defaults to a temp directory.
    """

    def __init__(self, headed: bool = False, screenshot_dir: str | None = None):
        self.headed = headed
        self.screenshot_dir = screenshot_dir or tempfile.mkdtemp(prefix="web_agent_")
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._console_errors: list[str] = []

    # -- Context manager support --

    def __enter__(self):
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -- Lifecycle --

    def launch(self):
        """Start the browser."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=not self.headed)
        self._context = self._browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()
        self._page.on("console", self._on_console)

    def close(self):
        """Shut down the browser."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    # -- Navigation --

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> PageResult:
        """Navigate to a URL and return a PageResult with a screenshot."""
        try:
            self._console_errors.clear()
            self._page.goto(url, wait_until=wait_until, timeout=30000)
            self._page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout:
            pass  # page may still be usable
        except Exception as e:
            return self._error_result(str(e))
        return self._build_result()

    # -- Interactions --

    def click(self, selector: str, timeout: int = 5000) -> PageResult:
        """Click an element matched by CSS selector or text."""
        try:
            self._console_errors.clear()
            # Try CSS selector first, fall back to text-based selector
            try:
                self._page.click(selector, timeout=timeout)
            except PlaywrightTimeout:
                self._page.get_by_text(selector, exact=False).first.click(
                    timeout=timeout
                )
            self._page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeout:
            pass
        except Exception as e:
            return self._error_result(f"Click failed on '{selector}': {e}")
        return self._build_result()

    def type_text(
        self, selector: str, text: str, clear: bool = True, timeout: int = 5000
    ) -> PageResult:
        """Type text into an input field."""
        try:
            self._console_errors.clear()
            el = self._page.locator(selector).first
            el.wait_for(state="visible", timeout=timeout)
            if clear:
                el.fill("")
            el.type(text, delay=50)
        except Exception as e:
            return self._error_result(f"Type failed on '{selector}': {e}")
        return self._build_result(include_elements=False)

    def press_key(self, key: str) -> PageResult:
        """Press a keyboard key (e.g., 'Enter', 'Tab')."""
        try:
            self._console_errors.clear()
            self._page.keyboard.press(key)
            self._page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeout:
            pass
        except Exception as e:
            return self._error_result(f"Key press failed '{key}': {e}")
        return self._build_result()

    def select_option(self, selector: str, value: str) -> PageResult:
        """Select an option from a <select> element."""
        try:
            self._console_errors.clear()
            self._page.select_option(selector, value)
        except Exception as e:
            return self._error_result(f"Select failed on '{selector}': {e}")
        return self._build_result(include_elements=False)

    # -- Waiting --

    def wait_for(self, selector: str, timeout: int = 5000) -> PageResult:
        """Wait for an element to appear on the page."""
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeout:
            return self._error_result(
                f"Timed out waiting for '{selector}' after {timeout}ms"
            )
        return self._build_result()

    # -- Screenshots --

    def screenshot(
        self, path: str | None = None, full_page: bool = True, selector: str | None = None
    ) -> str:
        """Take a screenshot and return the file path."""
        if path is None:
            path = os.path.join(self.screenshot_dir, "screenshot.png")

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        if selector:
            self._page.locator(selector).first.screenshot(path=path)
        else:
            self._page.screenshot(path=path, full_page=full_page)
        return path

    # -- Page Analysis --

    def get_interactive_elements(self) -> list[dict]:
        """Return a list of all interactive elements on the page.

        Each element includes its type, a CSS selector, visible text, and
        ARIA role. This is the primary way the agent "understands" the UI.
        """
        script = """
        () => {
            const seen = new Set();
            const elements = [];

            function getSelector(el) {
                if (el.id) return '#' + CSS.escape(el.id);
                if (el.name && el.tagName === 'INPUT') return `input[name="${el.name}"]`;
                if (el.name && el.tagName === 'SELECT') return `select[name="${el.name}"]`;
                if (el.name && el.tagName === 'TEXTAREA') return `textarea[name="${el.name}"]`;

                const tag = el.tagName.toLowerCase();
                const parent = el.parentElement;
                if (!parent) return tag;

                const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
                if (siblings.length === 1) return getSelector(parent) + ' > ' + tag;
                const idx = siblings.indexOf(el) + 1;
                return getSelector(parent) + ' > ' + tag + ':nth-child(' + idx + ')';
            }

            const selectors = [
                'a[href]',
                'button',
                'input',
                'select',
                'textarea',
                '[role="button"]',
                '[role="link"]',
                '[role="tab"]',
                '[role="menuitem"]',
                '[onclick]',
                '[tabindex]'
            ];

            for (const sel of selectors) {
                for (const el of document.querySelectorAll(sel)) {
                    const key = el.outerHTML.slice(0, 200);
                    if (seen.has(key)) continue;
                    seen.add(key);

                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;

                    const text = (el.innerText || el.value || el.placeholder || el.title || el.ariaLabel || '').trim().slice(0, 100);
                    const type = el.type || el.tagName.toLowerCase();

                    elements.push({
                        type: type,
                        selector: getSelector(el),
                        text: text,
                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                        tag: el.tagName.toLowerCase(),
                        input_type: el.type || null,
                        placeholder: el.placeholder || null,
                        name: el.name || null,
                        href: el.href || null,
                        disabled: el.disabled || false
                    });
                }
            }
            return elements;
        }
        """
        try:
            return self._page.evaluate(script)
        except Exception:
            return []

    def get_page_structure(self) -> dict:
        """Return a simplified DOM structure of the page."""
        script = """
        () => {
            function summarize(el, depth) {
                if (depth > 4) return null;
                const tag = el.tagName?.toLowerCase();
                if (!tag || ['script', 'style', 'noscript', 'svg'].includes(tag)) return null;

                const text = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
                    ? el.childNodes[0].textContent.trim().slice(0, 80) : '';

                const children = Array.from(el.children)
                    .map(c => summarize(c, depth + 1))
                    .filter(Boolean)
                    .slice(0, 20);

                const node = { tag };
                if (el.id) node.id = el.id;
                if (el.className && typeof el.className === 'string')
                    node.class = el.className.split(' ').slice(0, 3).join(' ');
                if (text) node.text = text;
                if (children.length) node.children = children;
                return node;
            }
            return summarize(document.body, 0);
        }
        """
        try:
            return self._page.evaluate(script) or {}
        except Exception:
            return {}

    def extract_text(self, selector: str | None = None) -> str:
        """Extract visible text from the page or a specific element."""
        try:
            if selector:
                el = self._page.locator(selector).first
                return el.inner_text()
            return self._page.inner_text("body")[:5000]
        except Exception:
            return ""

    # -- Internal helpers --

    def _on_console(self, msg):
        if msg.type == "error":
            self._console_errors.append(msg.text)

    def _build_result(self, include_elements: bool = True) -> PageResult:
        screenshot_path = self.screenshot()
        return PageResult(
            url=self._page.url,
            title=self._page.title(),
            screenshot_path=screenshot_path,
            interactive_elements=self.get_interactive_elements() if include_elements else [],
            page_text=self._page.inner_text("body")[:3000] if include_elements else "",
            console_errors=list(self._console_errors),
            success=True,
        )

    def _error_result(self, error: str) -> PageResult:
        screenshot_path = ""
        try:
            screenshot_path = self.screenshot()
        except Exception:
            pass
        return PageResult(
            url=self._page.url if self._page else "",
            title=self._page.title() if self._page else "",
            screenshot_path=screenshot_path,
            error=error,
            success=False,
        )


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Browser automation runner")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument(
        "--screenshot-dir", default=None, help="Directory for screenshots"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # navigate
    nav = sub.add_parser("navigate", help="Navigate to a URL")
    nav.add_argument("url")

    # screenshot
    ss = sub.add_parser("screenshot", help="Take a screenshot")
    ss.add_argument("url")
    ss.add_argument("-o", "--output", default="screenshot.png")
    ss.add_argument("--selector", default=None)
    ss.add_argument("--full-page", action="store_true", default=True)

    # elements
    el = sub.add_parser("elements", help="List interactive elements")
    el.add_argument("url")

    # extract
    ex = sub.add_parser("extract", help="Extract text from page")
    ex.add_argument("url")
    ex.add_argument("--selector", default=None)

    # structure
    st = sub.add_parser("structure", help="Get page DOM structure")
    st.add_argument("url")

    # run-script
    rs = sub.add_parser("run-script", help="Run a generated Python script file")
    rs.add_argument("script_path")

    args = parser.parse_args()

    with BrowserSession(
        headed=args.headed, screenshot_dir=args.screenshot_dir
    ) as browser:
        if args.command == "navigate":
            result = browser.navigate(args.url)
            print(result.to_json())

        elif args.command == "screenshot":
            browser.navigate(args.url)
            path = browser.screenshot(
                path=args.output,
                full_page=args.full_page,
                selector=args.selector,
            )
            print(json.dumps({"screenshot": path}))

        elif args.command == "elements":
            browser.navigate(args.url)
            elements = browser.get_interactive_elements()
            print(json.dumps(elements, indent=2))

        elif args.command == "extract":
            browser.navigate(args.url)
            text = browser.extract_text(selector=args.selector)
            print(text)

        elif args.command == "structure":
            browser.navigate(args.url)
            structure = browser.get_page_structure()
            print(json.dumps(structure, indent=2))

        elif args.command == "run-script":
            # Execute a generated script in the same browser context
            script_path = args.script_path
            with open(script_path) as f:
                code = f.read()
            exec(code, {"browser": browser, "PageResult": PageResult})


if __name__ == "__main__":
    main()
