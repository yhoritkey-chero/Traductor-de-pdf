import os
import sys
import glob
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import fitz  # PyMuPDF
from PIL import Image
from playwright.async_api import async_playwright

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

async def translate_images(image_paths, target_dir, log_callback, progress_callback):
    translated_paths = []
    async with async_playwright() as p:
        log_callback("Iniciando navegador...")
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(locale="es-ES")
        page = await context.new_page()

        total = len(image_paths)
        for i, img_path in enumerate(image_paths):
            log_callback(f"Traduciendo página {i+1} de {total}...")
            # Update progress
            progress_callback((i / total) * 100)
            
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
                    # Depending on locale, text could be different. Using a generic strategy
                    # There's usually an input[type=file] we can attach and then click
                    # Let's find the file input directly
                    file_input = page.locator("input[type='file']")
                    if await file_input.count() > 0:
                        await file_input.set_files(img_path)
                    else:
                        # try click strategy
                        await page.locator('text="Browse your files"').click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(img_path)
                
                # Wait for the "Download translation" button
                # Or simply wait for the translated image to render and then download
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
                log_callback(f"Página {i+1} traducida con éxito.")
                
            except Exception as e:
                log_callback(f"Error al traducir la página {i+1}: ignorando traducción... ({str(e)})")
                translated_paths.append(img_path)
                
        await browser.close()
        progress_callback(100.0)
    return translated_paths

def run_translation_process(pdf_path, output_pdf_path, temp_dir, log_callback, progress_callback, on_complete):
    try:
        log_callback(f"Iniciando el proceso para: {os.path.basename(pdf_path)}")
        doc = fitz.open(pdf_path)
        image_paths = []
        
        # 1. Convert to PNG
        log_callback("Paso 1: Convirtiendo el PDF a imágenes (PNG)...")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path = os.path.join(temp_dir, f"page_{page_num:03d}.png")
            pix.save(img_path)
            image_paths.append(img_path)
            
        log_callback(f"Se extrajeron {len(image_paths)} páginas.")
            
        # 2. Upload to Google Translate
        log_callback("Paso 2: Traduciendo imágenes con Google Traductor...")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        translated_images = loop.run_until_complete(translate_images(image_paths, temp_dir, log_callback, progress_callback))
        loop.close()
        
        # 3. Assemble PDF
        log_callback("Paso 3: Ensamblando nuevamente el PDF con las imágenes traducidas...")
        images = []
        for p in translated_images:
            try:
                img = Image.open(p).convert("RGB")
                images.append(img)
            except Exception as e:
                log_callback(f"No se pudo cargar la imagen {p}: {e}")
                
        if images:
            images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
            log_callback(f"✨ ¡PDF traducido exitosamente!\nGuardado en:\n{output_pdf_path}")
        else:
            log_callback("No se generó el PDF debido a errores.")
            
        # Cleanup
        log_callback("Limpiando archivos temporales...")
        for p in image_paths + translated_images:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except:
                pass

        on_complete(True)
    except Exception as e:
        log_callback(f"\nOcurrió un error inesperado:\n{str(e)}")
        on_complete(False)


class PDFTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traductor de PDF a Español")
        self.geometry("650x500")
        self.configure(padx=20, pady=20)
        self.resizable(False, False)
        
        self.pdf_file_path = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_lbl = tk.Label(self, text="Traductor de PDF con Google Translate", font=("Helvetica", 16, "bold"))
        title_lbl.pack(pady=(0, 20))
        
        # File selector frame
        file_frame = tk.Frame(self)
        file_frame.pack(fill=tk.X, pady=10)
        
        btn_select = tk.Button(file_frame, text="1. Seleccionar Archivo PDF...", font=("Helvetica", 11), command=self.select_file, bg="#0052cc", fg="white", cursor="hand2")
        btn_select.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_file = tk.Label(file_frame, text="Ningún archivo seleccionado.", font=("Helvetica", 10), fg="grey")
        self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action frame
        action_frame = tk.Frame(self)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.btn_translate = tk.Button(action_frame, text="2. Iniciar Traducción", font=("Helvetica", 12, "bold"), command=self.start_translation, bg="#28a745", fg="white", cursor="hand2", state=tk.DISABLED)
        self.btn_translate.pack(fill=tk.X)
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=15)
        
        # Logs
        log_lbl = tk.Label(self, text="Registro de actividades:", font=("Helvetica", 10, "bold"))
        log_lbl.pack(anchor=tk.W)
        
        self.txt_log = scrolledtext.ScrolledText(self, height=12, wrap=tk.WORD, font=("Consolas", 9))
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        self.txt_log.config(state=tk.DISABLED)
        
        # Temp dir creation
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.app_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def log(self, message):
        self.after(0, self._log_sync, message)
        
    def _log_sync(self, message):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.update_idletasks()
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=(("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*"))
        )
        if file_path:
            self.pdf_file_path = file_path
            self.lbl_file.config(text=os.path.basename(file_path), fg="black")
            self.btn_translate.config(state=tk.NORMAL)
            self.log(f"Archivo seleccionado: {file_path}")
            
    def update_progress(self, percent):
        self.after(0, self._update_progress_sync, percent)
        
    def _update_progress_sync(self, percent):
        self.progress_var.set(percent)
        self.update_idletasks()
        
    def start_translation(self):
        if not self.pdf_file_path:
            return
            
        output_path = filedialog.asksaveasfilename(
            title="Guardar PDF Traducido Como",
            defaultextension=".pdf",
            initialfile=f"traducido_{os.path.basename(self.pdf_file_path)}",
            filetypes=(("Archivos PDF", "*.pdf"),)
        )
        
        if not output_path:
            return
            
        self.btn_translate.config(state=tk.DISABLED)
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        threading.Thread(target=run_translation_process, args=(
            self.pdf_file_path, 
            output_path, 
            self.temp_dir, 
            self.log, 
            self.update_progress,
            self.on_translation_complete
        ), daemon=True).start()
        
    def on_translation_complete(self, success):
        self.after(0, self._on_translation_complete_sync, success)
        
    def _on_translation_complete_sync(self, success):
        self.btn_translate.config(state=tk.NORMAL)
        self.progress_var.set(100.0 if success else 0.0)
        if success:
            messagebox.showinfo("Completado", "El PDF fue traducido y guardado exitosamente.")
        else:
            messagebox.showerror("Error", "Ocurrió un error durante la traducción. Revisa el registro.")

if __name__ == "__main__":
    app = PDFTranslatorApp()
    app.mainloop()
