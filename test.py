import asyncio
import subprocess
import os

async def install_browsers_if_needed():
    if not os.path.exists("/app/.cache/ms-playwright"):
        print("▶ Installing Playwright Browsers...")
        subprocess.run(["playwright", "install", "chromium"], check=True)
    else:
        print("▶ Browsers already installed.")

# Example how you modify your function
from playwright.async_api import async_playwright
import re

async def scrape_amazon_with_playwright(url):
    await install_browsers_if_needed()  # 🛠 Install browsers first if missing
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=600000)
        text = await page.inner_text('body')
        await browser.close()
        return re.sub(r'\s+', ' ', text).strip()


# from playwright.async_api import async_playwright
# import re

# async def scrape_amazon_with_playwright(url):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         print("browser")
#         page = await browser.new_page()
#         print("page")
#         await page.goto(url, timeout=600000)
#         text = await page.inner_text('body')
#         print("text")
#         await browser.close()
#         return re.sub(r'\s+', ' ', text).strip()
