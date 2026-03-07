"""Data extraction helpers — text, tables, links, structured data."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_browser import BrowserSession


def extract_all_links(browser: BrowserSession) -> list[dict]:
    """Extract all links from the current page."""
    return browser._page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
            text: a.innerText.trim().slice(0, 100),
            href: a.href
        })).filter(l => l.text && l.href)
    """)


def extract_table(browser: BrowserSession, selector: str = "table") -> list[list[str]]:
    """Extract a table as a list of rows (each row is a list of cell strings)."""
    return browser._page.evaluate(f"""
        () => {{
            const table = document.querySelector('{selector}');
            if (!table) return [];
            return Array.from(table.querySelectorAll('tr')).map(row =>
                Array.from(row.querySelectorAll('td, th')).map(cell =>
                    cell.innerText.trim()
                )
            );
        }}
    """)


def extract_meta(browser: BrowserSession) -> dict:
    """Extract page metadata — title, description, og tags."""
    return browser._page.evaluate("""
        () => {
            const meta = {};
            meta.title = document.title;
            const desc = document.querySelector('meta[name="description"]');
            if (desc) meta.description = desc.content;
            for (const el of document.querySelectorAll('meta[property^="og:"]')) {
                meta[el.getAttribute('property')] = el.content;
            }
            return meta;
        }
    """)
