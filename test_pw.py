import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()
        
        await page.goto("https://translate.google.com/?sl=auto&tl=es&op=images", wait_until="networkidle")
        await asyncio.sleep(2)
        print("Uploading file...")
        await page.set_input_files('input[type="file"]', 'dummy.png')
        
        # Wait 5 seconds for translation
        await asyncio.sleep(5)
        
        print("Taking screenshot...")
        await page.screenshot(path="debug_screen.png")
        print("Screenshot saved.")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
