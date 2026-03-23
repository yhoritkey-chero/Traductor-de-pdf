import os
import sys
import glob
import asyncio
import argparse
import fitz  # PyMuPDF
from PIL import Image
from playwright.async_api import async_playwright

async def translate_images(image_paths, target_dir):
    translated_paths = []
    async with async_playwright() as p:
        # Launch browser. Headless=False helps if user needs to solve captcha initially.
        # But we'll use headless=True for automation stability, users can change it if needed.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()

        for img_path in image_paths:
            print(f"Translating {img_path}...")
            try:
                # Go to Google Translate image section
                await page.goto("https://translate.google.com/?sl=auto&tl=es&op=images", wait_until="networkidle")
                
                # Dismiss cookie consent if present
                try:
                    accept_btn = page.locator('button', has_text="Accept all")
                    if await accept_btn.count() > 0:
                        await accept_btn.first.click()
                except:
                    pass

                # Upload file via file chooser
                async with page.expect_file_chooser() as fc_info:
                    # Look for the 'Browse your files' button
                    await page.locator('text="Browse your files"').click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(img_path)
                
                # Wait for the "Download translation" button to appear
                # The translation process usually takes a few seconds
                download_btn = page.locator('button', has_text="Download translation")
                await download_btn.wait_for(state="visible", timeout=30000)
                
                async with page.expect_download() as download_info:
                    await download_btn.click()
                    
                download = await download_info.value
                base_name = os.path.basename(img_path)
                trans_path = os.path.join(target_dir, f"trans_{base_name}")
                await download.save_as(trans_path)
                translated_paths.append(trans_path)
                print(f"Saved translated image: {trans_path}")
                
            except Exception as e:
                print(f"Error translating {img_path}: {e}")
                # Fallback: copy the original if translation failed
                translated_paths.append(img_path)
                
        await browser.close()
    return translated_paths

def process_pdf(pdf_path, output_pdf_path, temp_dir):
    print(f"Processing PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    image_paths = []
    
    # 1. Convert to PNG
    print("1. Converting PDF to PNGs...")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 150 DPI is a good balance for text readability and image size
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = os.path.join(temp_dir, f"{os.path.basename(pdf_path)}_page_{page_num:03d}.png")
        pix.save(img_path)
        image_paths.append(img_path)
        
    # 2. Upload to Google Translate
    print("2. Translating PNGs on Google Translate...")
    translated_images = asyncio.run(translate_images(image_paths, temp_dir))
    
    # 3. Assemble PDF
    print("3. Assembling translated PNGs into PDF...")
    images = []
    for p in translated_images:
        try:
            img = Image.open(p).convert("RGB")
            images.append(img)
        except Exception as e:
            print(f"Could not open image {p}: {e}")
            
    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        print(f"Successfully generated translated PDF: {output_pdf_path}")
    else:
        print("No images were processed successfully.")
        
    # Cleanup temp images for this PDF
    for p in image_paths + translated_images:
        try:
            if os.path.exists(p):
                os.remove(p)
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Translate PDF via Google Translate Images")
    parser.add_argument("--watch", action="store_true", help="Watch the input folder for new PDFs")
    args = parser.parse_args()

    app_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(app_dir, "input")
    output_folder = os.path.join(app_dir, "output")
    temp_folder = os.path.join(app_dir, "temp")
    
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)
    
    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    
    if not pdf_files:
        print(f"Please place your PDF files in the '{input_folder}' directory and run script again.")
        sys.exit(0)
        
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        out_path = os.path.join(output_folder, f"es_{filename}")
        if os.path.exists(out_path):
            print(f"Skipping {filename}, already translated.")
            continue
        process_pdf(pdf_file, out_path, temp_folder)
        
    print("All PDFs processed!")

if __name__ == "__main__":
    main()
