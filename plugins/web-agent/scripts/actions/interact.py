"""Interaction helpers — click, type, select, scroll."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_browser import BrowserSession, PageResult


def fill_form(browser: BrowserSession, fields: dict[str, str]) -> PageResult:
    """Fill multiple form fields.

    Parameters
    ----------
    fields : dict
        Mapping of CSS selector to value to type.
    """
    result = None
    for selector, value in fields.items():
        result = browser.type_text(selector, value)
        if not result.success:
            return result
    return result


def click_button(browser: BrowserSession, text: str) -> PageResult:
    """Click a button by its visible text."""
    return browser.click(f"button:has-text('{text}')")


def scroll_down(browser: BrowserSession, pixels: int = 500) -> PageResult:
    """Scroll the page down by a number of pixels."""
    browser._page.evaluate(f"window.scrollBy(0, {pixels})")
    return browser._build_result()


def scroll_to_element(browser: BrowserSession, selector: str) -> PageResult:
    """Scroll until an element is visible."""
    try:
        browser._page.locator(selector).first.scroll_into_view_if_needed()
    except Exception as e:
        return browser._error_result(f"Scroll to '{selector}' failed: {e}")
    return browser._build_result()
