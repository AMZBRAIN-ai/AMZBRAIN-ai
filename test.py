from playwright.async_api import async_playwright
import re

async def scrape_amazon_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("browser")
        page = await browser.new_page()
        print("page")
        await page.goto(url, timeout=600000)
        text = await page.inner_text('body')
        print("text")
        await browser.close()
        return re.sub(r'\s+', ' ', text).strip()

# from playwright.sync_api import sync_playwright
# import re

# def scrape_amazon_with_playwright(url):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page()
#         page.goto(url, timeout=60000)
#         text = re.sub(r'\s+', ' ', page.inner_text('body')).strip()
#         browser.close()
#         return text

# # Usage
# # url = "https://www.amazon.com/Discovering-Constructions-Illustrated-Experimental-Construction/dp/B01D37PKM4"
# # print(scrape_amazon_with_playwright(url))
