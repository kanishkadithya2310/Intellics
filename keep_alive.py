"""Opens the Streamlit app in a real browser so it counts as a visit.
If the app is asleep, clicks the "get this app back up" button."""
import os
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = os.environ["APP_URL"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

    # 1. If the app is asleep, wake it
    try:
        btn = page.get_by_role("button", name="Yes, get this app back up!")
        btn.wait_for(timeout=15_000)
        btn.click()
        print("App was asleep -> wake-up button clicked")
    except PWTimeout:
        print("No sleep screen -> app was already awake")

    # 2. Wait until the app actually renders (it lives inside an iframe)
    try:
        app = page.frame_locator('iframe[title="streamlitApp"]')
        app.locator('[data-testid="stApp"]').wait_for(timeout=240_000)
        print("App is up and rendered")
    except PWTimeout:
        print("App did not load in time")
        browser.close()
        sys.exit(1)

    # 3. Stay connected briefly so the websocket session registers as activity
    page.wait_for_timeout(30_000)
    browser.close()
