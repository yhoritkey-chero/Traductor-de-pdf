import os
import sys
import asyncio
import tempfile
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
from playwright.async_api import async_playwright

@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

st.set_page_config(page_title="Traductor de PDF a Español", page_icon="📝", layout="centered")

async def translate_images(image_paths, target_dir, log_placeholder, progress_bar):
    translated_paths = []
    async with async_playwright() as p:
        log_placeholder.text("Iniciando navegador web (en segundo plano)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="es-ES")
        page = await context.new_page()

        total = len(image_paths)
        for i, img_path in enumerate(image_paths):
            log_placeholder.text(f"Traduciendo página {i+1} de {total}...")
            # Actualizamos progreso
            progress_bar.progress((i / total))
            
            try:
                # Ir a la sección de imágenes de Google Translate
                await page.goto("https://translate.google.com/?sl=auto&tl=es&op=images", wait_until="networkidle")
                
                # Aceptar cookies si aparece
                try:
                    accept_btn = page.locator('button', has_text="Accept all")
                    if await accept_btn.count() > 0:
                        await accept_btn.first.click()
                except:
                    pass

                # Subir archivo
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    await file_input.set_files(img_path)
                else:
                    async with page.expect_file_chooser(timeout=5000) as fc_info:
                        browse_btn = page.locator('button', has_text="Explorar tus archivos")
                        if await browse_btn.count() == 0:
                            browse_btn = page.locator('label', has_text="Browse your files")
                        if await browse_btn.count() == 0:
                            browse_btn = page.locator('text="Browse your files"')
                        await browse_btn.first.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(img_path)
                
                # Esperar el botón de descarga
                download_btn = page.locator('button', has_text="Descargar traducción")
                if await download_btn.count() == 0:
                   download_btn = page.locator('button', has_text="Download translation")

                await download_btn.wait_for(state="visible", timeout=45000)
                
                async with page.expect_download() as download_info:
                    await download_btn.click()
                    
                download = await download_info.value
                base_name = os.path.basename(img_path)
                trans_path = os.path.join(target_dir, f"trans_{base_name}")
                await download.save_as(trans_path)
                translated_paths.append(trans_path)
                
            except Exception as e:
                log_placeholder.text(f"Fallo en la página {i+1}, se añadirá en el idioma original.")
                translated_paths.append(img_path)
                
        await browser.close()
        progress_bar.progress(1.0)
    return translated_paths

def process_pdf(pdf_bytes, file_name, log_placeholder, progress_bar):
    # Usamos un directorio temporal para no dejar basura o problemas de concurrencia
    with tempfile.TemporaryDirectory() as temp_dir:
        input_pdf_path = os.path.join(temp_dir, file_name)
        output_pdf_path = os.path.join(temp_dir, f"es_{file_name}")
        
        # Guardamos los bytes del PDF que subió el usuario localmente
        with open(input_pdf_path, "wb") as f:
            f.write(pdf_bytes)
            
        try:
            log_placeholder.text(f"Procesando: {file_name}")
            doc = fitz.open(input_pdf_path)
            image_paths = []
            
            # 1. Extraer a PNG
            log_placeholder.text(f"Paso 1: Extrayendo {len(doc)} páginas del PDF a imágenes PNG...")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_path = os.path.join(temp_dir, f"page_{page_num:03d}.png")
                pix.save(img_path)
                image_paths.append(img_path)
                
            # 2. Traducir con Google
            log_placeholder.text("Paso 2: Traduciendo imágenes con Google Translate...")
            
            # Corregir error potencial de 'Event loop is closed' en Streamlit
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            translated_images = loop.run_until_complete(translate_images(image_paths, temp_dir, log_placeholder, progress_bar))
            
            # 3. Ensamblar PDF
            log_placeholder.text("Paso 3: Uniendo imágenes traducidas en un nuevo documento PDF...")
            images = []
            for p in translated_images:
                try:
                    img = Image.open(p).convert("RGB")
                    images.append(img)
                except Exception as e:
                    pass
                    
            if images:
                images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
                log_placeholder.text("¡PDF traducido con éxito!")
                
                # Devolvemos los bytes del PDF de salida
                with open(output_pdf_path, "rb") as f:
                    return f.read()
            else:
                log_placeholder.error("Error: no se pudo armar el PDF.")
                return None
                
        except Exception as e:
            log_placeholder.error(f"Error general: {e}")
            return None


def main():
    st.title("📝 Traductor de PDF Automático")
    st.write("Sube tu archivo PDF y la aplicación traducirá su contenido visual utilizando Google Translate y juntará las páginas en un nuevo documento PDF en español, sin que pierdas las imágenes y gráficos.")

    uploaded_file = st.file_uploader("Selecciona tu documento PDF", type=["pdf"])

    if uploaded_file is not None:
        if st.button("🚀 Iniciar Traducción"):
            
            # Elementos visuales dinámicos
            progress_bar = st.progress(0.0)
            log_placeholder = st.empty()
            
            with st.spinner("Realizando proceso completo. Esto puede tardar unos minutos..."):
                pdf_bytes = uploaded_file.read()
                translated_bytes = process_pdf(pdf_bytes, uploaded_file.name, log_placeholder, progress_bar)
                
            if translated_bytes:
                st.success("¡Traducción completada!")
                st.balloons()
                
                st.download_button(
                    label="💾 Descargar PDF Traducido",
                    data=translated_bytes,
                    file_name=f"es_{uploaded_file.name}",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
