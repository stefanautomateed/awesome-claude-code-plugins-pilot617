#!/usr/bin/env python3
"""Playwright-based CLI tool for taking screenshots and inspecting web page structure."""

import argparse
import json
import os
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright is not installed.", file=sys.stderr)
    print("Install it with: pip install playwright && python -m playwright install chromium", file=sys.stderr)
    sys.exit(1)


def take_screenshot(
    url,
    output="screenshot.png",
    selector=None,
    width=1400,
    height=900,
    full_page=True,
    wait_for=None,
    wait_seconds=2.0,
    device=None,
):
    """Take a screenshot of a web page or specific element."""
    with sync_playwright() as p:
        launch_args = {}
        context_args = {}

        if device:
            device_desc = p.devices.get(device)
            if device_desc:
                context_args.update(device_desc)
            else:
                print(f"Warning: device '{device}' not found, using default viewport", file=sys.stderr)
                context_args["viewport"] = {"width": width, "height": height}
        else:
            context_args["viewport"] = {"width": width, "height": height}

        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(**context_args)
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Error navigating to {url}: {e}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        if wait_for:
            try:
                page.wait_for_selector(wait_for, timeout=15000)
            except Exception as e:
                print(f"Warning: timed out waiting for selector '{wait_for}': {e}", file=sys.stderr)

        if wait_seconds > 0:
            page.wait_for_timeout(int(wait_seconds * 1000))

        if selector:
            element = page.query_selector(selector)
            if element:
                box = element.bounding_box()
                if box:
                    padding = 16
                    clip = {
                        "x": max(0, box["x"] - padding),
                        "y": max(0, box["y"] - padding),
                        "width": box["width"] + padding * 2,
                        "height": box["height"] + padding * 2,
                    }
                    page.screenshot(path=output, clip=clip)
                else:
                    print(f"Warning: could not get bounding box for '{selector}', taking full page", file=sys.stderr)
                    page.screenshot(path=output, full_page=full_page)
            else:
                print(f"Warning: selector '{selector}' not found, taking full page", file=sys.stderr)
                page.screenshot(path=output, full_page=full_page)
        else:
            page.screenshot(path=output, full_page=full_page)

        print(f"Screenshot saved to {output}")
        browser.close()


def screenshot_routes(base_url, routes_file, output_dir, width=1400, height=900, full_page=True, wait_seconds=2.0):
    """Screenshot multiple routes from a file, reusing a single browser instance."""
    if not os.path.isfile(routes_file):
        print(f"Error: routes file '{routes_file}' not found", file=sys.stderr)
        sys.exit(1)

    with open(routes_file) as f:
        routes = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not routes:
        print("No routes found in file", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        count = 0

        for route in routes:
            url = base_url.rstrip("/") + "/" + route.lstrip("/")
            filename = route.strip("/").replace("/", "_") or "index"
            output_path = os.path.join(output_dir, f"{filename}.png")

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                if wait_seconds > 0:
                    page.wait_for_timeout(int(wait_seconds * 1000))
                page.screenshot(path=output_path, full_page=full_page)
                print(f"  {output_path}")
                count += 1
            except Exception as e:
                print(f"  Error on {route}: {e}", file=sys.stderr)

        browser.close()
        print(f"\nCaptured {count}/{len(routes)} routes to {output_dir}")


def get_page_structure(url, width=1400, height=900, wait_for=None, wait_seconds=2.0, device=None):
    """Navigate to a URL and extract page structure as a dict."""
    with sync_playwright() as p:
        context_args = {}

        if device:
            device_desc = p.devices.get(device)
            if device_desc:
                context_args.update(device_desc)
            else:
                context_args["viewport"] = {"width": width, "height": height}
        else:
            context_args["viewport"] = {"width": width, "height": height}

        browser = p.chromium.launch()
        context = browser.new_context(**context_args)
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Error navigating to {url}: {e}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        if wait_for:
            try:
                page.wait_for_selector(wait_for, timeout=15000)
            except Exception as e:
                print(f"Warning: timed out waiting for '{wait_for}': {e}", file=sys.stderr)

        if wait_seconds > 0:
            page.wait_for_timeout(int(wait_seconds * 1000))

        structure = page.evaluate("""() => {
            const meta = {
                title: document.title || '',
                description: (document.querySelector('meta[name="description"]') || {}).content || '',
                viewport: (document.querySelector('meta[name="viewport"]') || {}).content || ''
            };

            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
                tag: h.tagName.toLowerCase(),
                text: h.textContent.trim()
            }));

            const links = Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }));

            const buttons = Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"]')).map(b => ({
                text: b.textContent.trim() || b.value || '',
                tag: b.tagName.toLowerCase(),
                disabled: b.disabled || false
            }));

            const forms = Array.from(document.querySelectorAll('form')).map(f => ({
                action: f.action || '',
                method: f.method || 'get',
                fields: Array.from(f.querySelectorAll('input, select, textarea')).map(field => ({
                    type: field.type || field.tagName.toLowerCase(),
                    name: field.name || '',
                    placeholder: field.placeholder || '',
                    required: field.required || false
                }))
            }));

            const images = Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.getAttribute('src') || '',
                alt: img.alt || '',
                width: img.naturalWidth,
                height: img.naturalHeight
            }));

            return { meta, headings, links, buttons, forms, images };
        }""")

        browser.close()
        return structure


def main():
    parser = argparse.ArgumentParser(description="Take screenshots and inspect web page structure using Playwright")
    parser.add_argument("url", help="URL to capture")
    parser.add_argument("-o", "--output", default="screenshot.png", help="Output file path (default: screenshot.png)")
    parser.add_argument("--selector", help="CSS selector for element capture")
    parser.add_argument("--width", type=int, default=1400, help="Viewport width (default: 1400)")
    parser.add_argument("--height", type=int, default=900, help="Viewport height (default: 900)")
    parser.add_argument("--full-page", dest="full_page", action="store_true", default=True, help="Capture full page (default)")
    parser.add_argument("--no-full-page", dest="full_page", action="store_false", help="Capture only the viewport")
    parser.add_argument("--wait-for", help="CSS selector to wait for before capture")
    parser.add_argument("--wait", type=float, default=2.0, help="Seconds to wait after load (default: 2.0)")
    parser.add_argument("--routes", help="Path to file with routes (one per line) for batch capture")
    parser.add_argument("--device", help="Playwright device name for emulation (e.g., 'iPhone 13')")
    parser.add_argument("--structure", action="store_true", help="Print page structure as JSON instead of taking a screenshot")

    args = parser.parse_args()

    if args.structure:
        structure = get_page_structure(
            url=args.url,
            width=args.width,
            height=args.height,
            wait_for=args.wait_for,
            wait_seconds=args.wait,
            device=args.device,
        )
        print(json.dumps(structure, indent=2))
    elif args.routes:
        screenshot_routes(
            base_url=args.url,
            routes_file=args.routes,
            output_dir=args.output,
            width=args.width,
            height=args.height,
            full_page=args.full_page,
            wait_seconds=args.wait,
        )
    else:
        take_screenshot(
            url=args.url,
            output=args.output,
            selector=args.selector,
            width=args.width,
            height=args.height,
            full_page=args.full_page,
            wait_for=args.wait_for,
            wait_seconds=args.wait,
            device=args.device,
        )


if __name__ == "__main__":
    main()
