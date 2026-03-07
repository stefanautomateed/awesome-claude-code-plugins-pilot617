"""Navigation helpers — go to URLs, follow links, handle redirects."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_browser import BrowserSession, PageResult


def navigate_and_screenshot(
    url: str, output: str = "page.png", headed: bool = False
) -> PageResult:
    """Navigate to a URL, take a screenshot, and return the result."""
    with BrowserSession(headed=headed) as browser:
        result = browser.navigate(url)
        if result.success:
            browser.screenshot(path=output)
            result.screenshot_path = output
        return result


def follow_link(browser: BrowserSession, link_text: str) -> PageResult:
    """Click a link by its visible text."""
    return browser.click(f"a:has-text('{link_text}')")


def go_back(browser: BrowserSession) -> PageResult:
    """Navigate back in browser history."""
    browser._page.go_back()
    return browser._build_result()
