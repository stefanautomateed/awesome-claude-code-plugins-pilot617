"""Authentication helpers — detect login pages and fill credentials."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_browser import BrowserSession, PageResult


def detect_login_page(browser: BrowserSession) -> dict:
    """Detect whether the current page is a login/sign-in page.

    Returns a dict with:
        is_login: bool
        username_selector: str | None
        password_selector: str | None
        submit_selector: str | None
    """
    return browser._page.evaluate("""
        () => {
            const result = {
                is_login: false,
                username_selector: null,
                password_selector: null,
                submit_selector: null
            };

            // Check for password field — strongest signal
            const pwField = document.querySelector('input[type="password"]');
            if (!pwField) return result;

            result.is_login = true;
            result.password_selector = pwField.id
                ? '#' + pwField.id
                : pwField.name
                    ? `input[name="${pwField.name}"]`
                    : 'input[type="password"]';

            // Find the username/email field — usually appears before the password
            const form = pwField.closest('form') || document.body;
            const inputs = Array.from(form.querySelectorAll(
                'input[type="text"], input[type="email"], input:not([type])'
            ));
            const userField = inputs.find(i => {
                const n = (i.name + i.id + i.placeholder + i.ariaLabel).toLowerCase();
                return /user|email|login|account/.test(n);
            }) || inputs[0];

            if (userField) {
                result.username_selector = userField.id
                    ? '#' + userField.id
                    : userField.name
                        ? `input[name="${userField.name}"]`
                        : null;
            }

            // Find submit button
            const submit = form.querySelector(
                'button[type="submit"], input[type="submit"], button:not([type])'
            );
            if (submit) {
                result.submit_selector = submit.id
                    ? '#' + submit.id
                    : submit.name
                        ? `[name="${submit.name}"]`
                        : 'button[type="submit"], input[type="submit"]';
            }

            return result;
        }
    """)


def login(
    browser: BrowserSession,
    username: str,
    password: str,
    username_selector: str | None = None,
    password_selector: str | None = None,
    submit_selector: str | None = None,
) -> PageResult:
    """Fill and submit a login form.

    If selectors are not provided, auto-detects them.
    """
    if not username_selector or not password_selector:
        detected = detect_login_page(browser)
        if not detected["is_login"]:
            return browser._error_result("No login form detected on this page")
        username_selector = username_selector or detected["username_selector"]
        password_selector = password_selector or detected["password_selector"]
        submit_selector = submit_selector or detected["submit_selector"]

    if username_selector:
        browser.type_text(username_selector, username)
    browser.type_text(password_selector, password)

    if submit_selector:
        return browser.click(submit_selector)
    else:
        return browser.press_key("Enter")
