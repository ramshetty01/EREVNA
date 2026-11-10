"""Explicit browser smoke check of an already running app (may call its provider)."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--output", type=Path, default=Path("artifacts/browser"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.goto(args.url, wait_until="networkidle")
        page.get_by_role("button", name="Start research").wait_for(timeout=20_000)
        page.screenshot(path=str(args.output / "home.png"), full_page=True)
        page.get_by_role("button", name="Start research").click()
        page.get_by_role("button", name="Download report").wait_for(timeout=120_000)
        page.get_by_role("heading", name="Findings", exact=True).wait_for()
        page.screenshot(path=str(args.output / "report.png"), full_page=True)
        page.get_by_role("tab", name="Evidence", exact=True).click()
        page.get_by_text("These are the passages provided to the model.", exact=False).wait_for()
        page.screenshot(path=str(args.output / "evidence.png"), full_page=True)
        page.get_by_role("tab", name="Run details", exact=True).click()
        with page.expect_download() as download:
            page.get_by_role("button", name="Download full run JSON").click()
        download.value.save_as(str(args.output / "run.json"))
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("tab", name="Report", exact=True).click()
        assert page.evaluate("document.documentElement.scrollWidth") <= 390
        page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
        browser.close()
    print(f"Browser flow, evidence, download and mobile checks passed. Artifacts: {args.output}")


if __name__ == "__main__":
    main()
