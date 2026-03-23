import asyncio
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()
        
        await page.goto("https://translate.google.com/?sl=auto&tl=es&op=images", wait_until="networkidle")
        
        # Create dummy image with text
        img = Image.new('RGB', (800, 600), color = 'white')
        d = ImageDraw.Draw(img)
        d.text((50,50), "Hello world, this is a test page.", fill=(0,0,0))
        d.text((50,150), "I want to see if the download button appears.", fill=(0,0,0))
        img.save('dummy_text.png')

        print("Uploading file...")
        await page.set_input_files('input[type="file"]', 'dummy_text.png')
        
        await asyncio.sleep(8)
        
        print("Taking screenshot after translate...")
        await page.screenshot(path="debug_screen2.png")
        print("Screenshot 2 saved.")
        
        # also print buttons
        buttons = await page.locator("button").all()
        for i, btn in enumerate(buttons):
            try:
                aria = await btn.get_attribute("aria-label")
                text = await btn.inner_text()
                if "download" in (aria or "").lower() or "download" in (text or "").lower():
                    print(f"FOUND DOWNLOAD BTN: aria='{aria}', text='{text}'")
                elif "descargar" in (aria or "").lower() or "descargar" in (text or "").lower():
                    print(f"FOUND DOWNLOAD BTN: aria='{aria}', text='{text}'")                    
            except Exception as e:
                pass

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
