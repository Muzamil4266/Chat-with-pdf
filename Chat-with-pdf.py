import os
import sys
import subprocess
import importlib

# === CLEAN STARTUP ===
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger().setLevel(logging.ERROR)

# =======================================================================
# AUTO-INSTALLER WITH PROGRESS GUI
# =======================================================================
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "pypdf": "pypdf",
    "rank_bm25": "rank-bm25",
    "sentence_transformers": "sentence-transformers",
    "numpy": "numpy",
    "PIL": "pillow",
    "pytesseract": "pytesseract",
    "pdf2image": "pdf2image",
}

def check_and_install_packages():
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append((import_name, pip_name))
    return missing

def install_packages_auto(packages, progress_callback=None):
    total = len(packages)
    for i, (import_name, pip_name) in enumerate(packages):
        pct = int((i / total) * 50)
        if progress_callback:
            progress_callback(f"Installing {pip_name}... ({i+1}/{total})", pct)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, 
                                   "--quiet", "--disable-pip-version-check"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            if progress_callback:
                progress_callback(f"Failed to install {pip_name}: {str(e)[:50]}", pct)
            raise Exception(f"Failed to install {pip_name}: {e}")
    if progress_callback:
        progress_callback("All packages installed!", 50)

# =======================================================================
# INSTALLER GUI (standard tkinter - no external deps)
# =======================================================================
def show_installer_gui(missing_packages):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("📦 Installing Dependencies")
    root.geometry("500x250")
    root.configure(bg="#0a0a1a")
    root.resizable(False, False)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"+{(screen_w-500)//2}+{(screen_h-250)//2}")

    tk.Label(root, text="📦 Installing Required Packages", font=("Segoe UI", 16, "bold"),
             fg="#00d4ff", bg="#0a0a1a").pack(pady=15)

    status_lbl = tk.Label(root, text="Preparing installation...", font=("Segoe UI", 11),
                          fg="#e8e8f0", bg="#0a0a1a")
    status_lbl.pack(pady=5)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TProgressbar", thickness=15, troughcolor="#1a1a2e",
                    background="#00d4ff", bordercolor="#1a1a2e")
    progress = ttk.Progressbar(root, mode="determinate", maximum=100, length=450)
    progress.pack(pady=15)
    progress["value"] = 0

    pkg_lbl = tk.Label(root, text="Packages: " + ", ".join([p[1] for p in missing_packages]),
                       font=("Segoe UI", 9), fg="#6a6a9e", bg="#0a0a1a", wraplength=480)
    pkg_lbl.pack(pady=5)

    def update_progress(msg, pct):
        root.after(0, lambda: _update(msg, pct))

    def _update(msg, pct):
        status_lbl.config(text=msg)
        progress["value"] = pct
        root.update()

    def do_install():
        try:
            install_packages_auto(missing_packages, progress_callback=update_progress)
            status_lbl.config(text="✅ Installation complete! Launching app...", fg="#00ff9d")
            progress["value"] = 100
            root.update()
            root.after(1000, root.destroy)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Installation Failed", str(e))
            root.destroy()
            sys.exit(1)

    root.after(500, do_install)
    root.mainloop()

# =======================================================================
# CHECK & INSTALL
# =======================================================================
missing = check_and_install_packages()
if missing:
    print(f"Missing packages: {[p[1] for p in missing]}")
    print("Launching installer GUI...")
    show_installer_gui(missing)
    still_missing = check_and_install_packages()
    if still_missing:
        print(f"Still missing: {[p[1] for p in still_missing]}")
        sys.exit(1)

# =======================================================================
# NOW IMPORT EVERYTHING
# =======================================================================
import re
import threading
import io
import time
import numpy as np
import json
import urllib.request
import urllib.error
import zipfile
import shutil

import customtkinter as ctk
from tkinter import filedialog, messagebox

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

_stderr_backup = sys.stderr
sys.stderr = io.StringIO()
from sentence_transformers import SentenceTransformer, CrossEncoder, util
sys.stderr = _stderr_backup

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

SETTINGS_FILE = "pdf_app_settings.json"
MAX_PAGES = 5000

DEFAULT_SETTINGS = {
    "theme": "dark",
    "accent_color": "#ff0040",
    "ocr_mode": False,
    "font_family": "Segoe UI",
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                for key, val in DEFAULT_SETTINGS.items():
                    if key not in loaded:
                        loaded[key] = val
                return loaded
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


# =======================================================================
# AI SEARCH ENGINE
# =======================================================================
class PDFSearchEngine:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self._safe_progress("Loading Retrieval Model (Sentence Transformer)...", 5)
        self.retrieval_model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
        self._safe_progress("Loading Cross-Encoder (Re-ranker)...", 60)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self._safe_progress("AI Engines Ready!", 100)
        self.sentences = []
        self.embeddings = None
        self.bm25 = None

    def _safe_progress(self, msg, pct):
        if self.progress_callback:
            try:
                self.progress_callback(msg, pct)
            except:
                pass

    def _download_with_progress(self, url, dest_path, progress_callback=None, start_pct=0, end_pct=100, label="Downloading"):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/octet-stream,application/zip,*/*'
        }
        max_retries = 3
        chunk_size = 8192
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    with open(dest_path, 'wb') as f:
                        downloaded = 0
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and progress_callback:
                                pct = start_pct + int((downloaded / total_size) * (end_pct - start_pct))
                                progress_callback(f"{label}: {downloaded//1024:,} KB / {total_size//1024:,} KB ({pct}%)", pct)
                            elif progress_callback:
                                progress_callback(f"{label}: {downloaded//1024:,} KB", start_pct + (end_pct - start_pct)//2)
                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                    return True
                else:
                    raise ValueError("Downloaded file is empty")
            except Exception as e:
                if attempt < max_retries - 1:
                    if progress_callback:
                        progress_callback(f"Retrying download (attempt {attempt+2})...", start_pct)
                    time.sleep(2)
                else:
                    raise Exception(f"Download failed after {max_retries} attempts: {str(e)}")
        return False

    def _ensure_tesseract(self, progress_callback=None):
        if shutil.which("tesseract") is not None:
            return True
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        local_tesseract = os.path.join(base_path, "tesseract", "tesseract.exe")
        if os.path.exists(local_tesseract):
            pytesseract.pytesseract.tesseract_cmd = local_tesseract
            return True
        if progress_callback:
            progress_callback("Preparing Tesseract download...", 5)
        tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-portable-5.4.0.20240606.zip"
        download_dir = os.path.join(base_path, "tesseract")
        os.makedirs(download_dir, exist_ok=True)
        zip_path = os.path.join(download_dir, "tesseract.zip")
        try:
            if progress_callback:
                progress_callback("Downloading Tesseract OCR (~40 MB)...", 10)
            self._download_with_progress(tesseract_url, zip_path, progress_callback=progress_callback, start_pct=10, end_pct=60, label="Downloading Tesseract")
            if progress_callback:
                progress_callback("Extracting Tesseract...", 60)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_dir)
            os.remove(zip_path)
            for root, dirs, files in os.walk(download_dir):
                if "tesseract.exe" in files:
                    pytesseract.pytesseract.tesseract_cmd = os.path.join(root, "tesseract.exe")
                    if progress_callback:
                        progress_callback("Tesseract OCR Ready!", 100)
                    return True
            raise FileNotFoundError("tesseract.exe not found")
        except Exception as e:
            raise Exception(f"Tesseract setup failed: {str(e)}")

    def load_and_index_pdf(self, file_path, progress_callback=None, use_ocr=False):
        if use_ocr and OCR_AVAILABLE:
            text = self._ocr_extract(file_path, progress_callback)
        elif use_ocr and not OCR_AVAILABLE:
            raise ImportError("OCR libraries not installed. Run: pip install pytesseract pdf2image pillow")
        else:
            text = self._normal_extract(file_path, progress_callback)
        if not text or len(text.strip()) < 50:
            raise ValueError("No extractable text found. Try OCR mode for scanned PDFs.")
        if progress_callback:
            progress_callback("Cleaning text...", 52)
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        if progress_callback:
            progress_callback("Splitting sentences...", 55)
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        raw_sentences = [s.strip() for s in raw_sentences if len(s.strip().split()) >= 4]
        self.sentences = []
        for i in range(len(raw_sentences) - 1):
            combined = f"{raw_sentences[i]} {raw_sentences[i+1]}"
            combined = re.sub(r'\s+', ' ', combined)
            self.sentences.append(combined)
        if not self.sentences:
            self.sentences = raw_sentences
        if not self.sentences:
            raise ValueError("No extractable text found in this PDF.")
        if progress_callback:
            progress_callback("Building keyword index...", 60)
        tokenized_corpus = [doc.lower().split(" ") for doc in self.sentences]
        self.bm25 = BM25Okapi(tokenized_corpus)
        if progress_callback:
            progress_callback("Encoding vectors (0%)...", 65)
        embeddings_list = []
        batch_size = 32
        total = len(self.sentences)
        for batch_num in range(0, total, batch_size):
            batch = self.sentences[batch_num:batch_num + batch_size]
            batch_emb = self.retrieval_model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_emb)
            if progress_callback:
                pct = 65 + int((batch_num + batch_size) / total * 35)
                pct = min(pct, 100)
                progress_callback(f"Encoding vectors: {min(batch_num+batch_size, total)}/{total} ({pct}%)", pct)
        self.embeddings = np.vstack(embeddings_list)
        if progress_callback:
            progress_callback("Indexing complete! 100%", 100)

    def _normal_extract(self, file_path, progress_callback=None):
        reader = PdfReader(file_path)
        text = ""
        total_pages = min(len(reader.pages), MAX_PAGES)
        for i in range(total_pages):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + " "
            except:
                pass
            if progress_callback:
                pct = int((i + 1) / total_pages * 50)
                progress_callback(f"Reading page {i+1}/{total_pages} ({pct}%)", pct)
        if progress_callback:
            progress_callback(f"Extracted {total_pages} pages (50%)", 50)
        return text

    def _ocr_extract(self, file_path, progress_callback=None):
        if not OCR_AVAILABLE:
            raise ImportError("OCR libraries not installed.")
        if progress_callback:
            progress_callback("Checking OCR engine...", 2)
        self._ensure_tesseract(progress_callback=progress_callback)
        if progress_callback:
            progress_callback("Converting PDF to images...", 30)
        images = convert_from_path(file_path, first_page=1, last_page=min(MAX_PAGES, 500))
        total = len(images)
        text = ""
        for i, image in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(image)
                if page_text:
                    text += page_text + " "
            except:
                pass
            if progress_callback:
                pct = 30 + int((i + 1) / total * 20)
                progress_callback(f"OCR scanning page {i+1}/{total} ({pct}%)", pct)
        if progress_callback:
            progress_callback(f"OCR complete: {total} pages (50%)", 50)
        return text

    def search(self, user_query):
        if not self.sentences or self.embeddings is None:
            return "Engine not ready. Please index a PDF first.", 0.0
        query_emb = self.retrieval_model.encode([user_query], show_progress_bar=False)
        vector_scores = util.cos_sim(query_emb, self.embeddings).numpy().flatten()
        top_vector_idx = np.argsort(vector_scores)[-10:][::-1]
        query_lower = user_query.lower().split(" ")
        bm25_scores = self.bm25.get_scores(query_lower)
        top_keyword_idx = np.argsort(bm25_scores)[-5:][::-1]
        candidate_indices = list(set(list(top_vector_idx) + list(top_keyword_idx)))
        pairs = [[user_query, self.sentences[idx]] for idx in candidate_indices]
        cross_scores = self.reranker.predict(pairs)
        final_scores = 1 / (1 + np.exp(-cross_scores)) * 100
        best_local_idx = np.argmax(final_scores)
        best_global_idx = candidate_indices[best_local_idx]
        return self.sentences[best_global_idx], final_scores[best_local_idx]

# =======================================================================
# CUSTOMTKINTER MAIN APP
# =======================================================================
class PDFSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat With PDF")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.settings = load_settings()
        self.engine = None
        self.selected_file_path = None
        self.ocr_mode = self.settings.get("ocr_mode", False)
        self.is_processing = False
        self.build_ui()
        self.root.after(500, self.start_model_loading)

    def build_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # === OCR INSTRUCTIONS CARD ===
        ocr_card = ctk.CTkFrame(self.main_frame, fg_color="#1a0a1a", corner_radius=15, border_color="#ff0040", border_width=2)
        ocr_card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(ocr_card, text="📦 Manual Tesseract OCR Installation", font=("Segoe UI", 13, "bold"), text_color="#ff0040").pack(anchor="w", padx=15, pady=(10, 5))

        instructions = """If automatic download fails when you click OCR Mode, do this:

1. Download from: https://github.com/UB-Mannheim/tesseract/releases
   Get the file: tesseract-ocr-w64-portable-5.4.0.20240606.zip
2. Extract the ZIP file anywhere on your computer.
3. Find your app folder. Open _internal folder next to Chat_With_PDF.exe.
4. Copy the extracted tesseract folder into _internal.
   Final path must be: _internal/tesseract/tesseract.exe
5. Restart the app. Click OCR Mode. Done."""

        instructions_box = ctk.CTkTextbox(
        ocr_card,
        height=80,
        font=("Segoe UI", 10)
         )
        instructions_box.pack(fill="x", padx=15, pady=(0, 10))

        instructions_box.insert("1.0", instructions)
        instructions_box.configure(state="disabled")

        header = ctk.CTkFrame(self.main_frame, fg_color="#1a0a1a", corner_radius=15)
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="🔮 Chat With PDF", font=("Segoe UI", 24, "bold"), text_color="#ff0040").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(header, text="AI-Powered PDF Analysis", font=("Segoe UI", 12), text_color="#b04bff").pack(side="left", padx=5)
        self.settings_btn = ctk.CTkButton(header, text="⚙️", width=40, height=40, corner_radius=10, fg_color="#2a0a2a", hover_color="#4a0a4a", command=self.open_settings)
        self.settings_btn.pack(side="right", padx=15)

        mode_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        mode_card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(mode_card, text="◈ EXTRACTION MODE", font=("Segoe UI", 12, "bold"), text_color="#ff0040").pack(anchor="w", padx=15, pady=(10, 5))
        btn_frame = ctk.CTkFrame(mode_card, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=15, pady=5)
        self.normal_btn = ctk.CTkButton(btn_frame, text="📄 NORMAL", font=("Segoe UI", 12, "bold"), width=140, height=40, corner_radius=10, command=lambda: self.set_mode(False))
        self.normal_btn.pack(side="left", padx=(0, 10))
        self.ocr_btn = ctk.CTkButton(btn_frame, text="🔍 OCR", font=("Segoe UI", 12, "bold"), width=140, height=40, corner_radius=10, fg_color="#2a0a2a", hover_color="#4a0a4a", command=lambda: self.set_mode(True))
        self.ocr_btn.pack(side="left")
        ctk.CTkLabel(mode_card, text="• Normal: Best for text-based PDFs  • OCR: Use for scanned documents\n• Ask matching questions for accurate results  • Confidence score shown after each answer",
                     font=("Segoe UI", 10), text_color="#b04bff", justify="left").pack(anchor="w", padx=15, pady=(5, 10))

        doc_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        doc_card.pack(fill="x", pady=(0, 15))
        doc_inner = ctk.CTkFrame(doc_card, fg_color="transparent")
        doc_inner.pack(fill="x", padx=15, pady=15)
        self.file_btn = ctk.CTkButton(doc_inner, text="📂 SELECT PDF", font=("Segoe UI", 13, "bold"), width=180, height=45, corner_radius=12, command=self.start_file_loading)
        self.file_btn.pack(side="left")
        self.file_lbl = ctk.CTkLabel(doc_inner, text="⚡ Initializing AI engines...", font=("Segoe UI", 12, "bold"), text_color="#b04bff")
        self.file_lbl.pack(side="left", fill="x", expand=True, padx=(20, 10))

        self.progress_card = ctk.CTkFrame(self.main_frame, fg_color="#0d0a0d", corner_radius=10)
        self.progress_lbl = ctk.CTkLabel(self.progress_card, text="Ready", font=("Segoe UI", 11), text_color="#e8e8f0")
        self.progress_lbl.pack(anchor="w", padx=15, pady=(10, 0))
        self.progress_bar = ctk.CTkProgressBar(self.progress_card, width=900, height=12, corner_radius=6, progress_color="#ff0040", fg_color="#2a0a2a")
        self.progress_bar.pack(fill="x", padx=15, pady=(5, 10))
        self.progress_bar.set(0)

        search_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        search_card.pack(fill="x", pady=(0, 15))
        search_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=15)
        self.mode_indicator = ctk.CTkLabel(search_inner, text="📄 MODE: NORMAL (Standard Document Parsing)", font=("Segoe UI", 11, "bold"), text_color="#00ff9d")
        self.mode_indicator.pack(anchor="w", pady=(0, 10))
        query_frame = ctk.CTkFrame(search_inner, fg_color="transparent")
        query_frame.pack(fill="x")
        self.query_entry = ctk.CTkEntry(query_frame, font=("Segoe UI", 13), height=45, corner_radius=10, placeholder_text="Ask a question about your PDF...", border_color="#4a0a4a", border_width=2)
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.trigger_search())
        self.search_btn = ctk.CTkButton(query_frame, text="🔍 SEARCH", font=("Segoe UI", 12, "bold"), width=120, height=45, corner_radius=10, command=self.trigger_search)
        self.search_btn.pack(side="right")

        output_card = ctk.CTkFrame(self.main_frame, fg_color="#0d0a0d", corner_radius=15)
        output_card.pack(fill="both", expand=True)
        output_header = ctk.CTkFrame(output_card, fg_color="transparent")
        output_header.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkLabel(output_header, text="◈ SEARCH RESULTS", font=("Segoe UI", 11, "bold"), text_color="#ff0040").pack(side="left")
        self.output_text = ctk.CTkTextbox(output_card, font=("Segoe UI", 12), wrap="word", fg_color="#0d0a0d", text_color="#e8e8f0", corner_radius=10, border_color="#4a0a4a", border_width=1)
        self.output_text.pack(fill="both", expand=True, padx=15, pady=10)

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Ready", font=("Segoe UI", 10), text_color="#b04bff")
        self.status_bar.pack(fill="x", pady=(10, 0))
        self.update_mode_buttons()

    def _show_progress(self, message="Initializing..."):
        self.progress_card.pack(fill="x", pady=(0, 5), after=self.main_frame.winfo_children()[2])
        self.progress_lbl.configure(text=message)
        self.progress_bar.set(0)
        self.root.update()

    def _hide_progress(self):
        self.progress_card.pack_forget()
        self.root.update()

    def _update_progress(self, message, percentage):
        self.progress_lbl.configure(text=message)
        self.progress_bar.set(percentage / 100.0)
        self.status_bar.configure(text=f"⏳ {message}")
        self.root.update()

    def update_mode_buttons(self):
        if self.ocr_mode:
            self.ocr_btn.configure(fg_color="#ff0040", text_color="#0a0a1a", hover_color="#cc0033")
            self.normal_btn.configure(fg_color="#2a0a2a", text_color="#e8e8f0", hover_color="#4a0a4a")
            self.mode_indicator.configure(text="🔍 MODE: OCR (Scanned PDFs)", text_color="#ffd166")
        else:
            self.normal_btn.configure(fg_color="#ff0040", text_color="#0a0a1a", hover_color="#cc0033")
            self.ocr_btn.configure(fg_color="#2a0a2a", text_color="#e8e8f0", hover_color="#4a0a4a")
            self.mode_indicator.configure(text="📄 MODE: NORMAL (Standard Document Parsing)", text_color="#00ff9d")

    def set_mode(self, use_ocr):
        if use_ocr:
            if self._check_ocr_ready():
                self.ocr_mode = True
                self.settings["ocr_mode"] = True
                save_settings(self.settings)
                self.update_mode_buttons()
                return
            if messagebox.askyesno("OCR Engine Required", "OCR requires Tesseract OCR (~40 MB).\n\nDownload and install it now?"):
                self.set_ui_state("disabled")
                self._show_progress("Preparing OCR download...")
                self.progress_bar.set(0)
                def run_install():
                    try:
                        self.engine._ensure_tesseract(progress_callback=self._update_progress)
                        self.root.after(0, self.ocr_install_done, True)
                    except Exception as e:
                        self.root.after(0, self.ocr_install_done, False, str(e))
                threading.Thread(target=run_install, daemon=True).start()
            else:
                self.ocr_mode = False
                self.settings["ocr_mode"] = False
                save_settings(self.settings)
                self.update_mode_buttons()
        else:
            self.ocr_mode = False
            self.settings["ocr_mode"] = False
            save_settings(self.settings)
            self.update_mode_buttons()

    def ocr_install_done(self, success, err_msg=""):
        self._hide_progress()
        self.set_ui_state("normal")
        if success:
            messagebox.showinfo("Success", "OCR Ready!")
            self.ocr_mode = True
            self.settings["ocr_mode"] = True
            save_settings(self.settings)
            self.update_mode_buttons()
            self.status_bar.configure(text="✅ OCR Engine Activated")
        else:
            messagebox.showerror("Error", f"OCR setup failed:\n{err_msg}")
            self.ocr_mode = False
            self.settings["ocr_mode"] = False
            save_settings(self.settings)
            self.update_mode_buttons()

    def _check_ocr_ready(self):
        if not OCR_AVAILABLE:
            return False
        return shutil.which("tesseract") is not None or os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tesseract", "tesseract.exe"))

    def set_ui_state(self, state):
        states = {"normal": "normal", "disabled": "disabled"}
        self.file_btn.configure(state=states.get(state, state))
        self.search_btn.configure(state=states.get(state, state))
        self.query_entry.configure(state=states.get(state, state))
        self.normal_btn.configure(state=states.get(state, state))
        self.ocr_btn.configure(state=states.get(state, state))

    def start_model_loading(self):
        self._show_progress("Starting AI engines... (First run downloads ~150 MB models)")
        self.progress_bar.set(0.05)
        threading.Thread(target=self.async_model_load, daemon=True).start()

    def async_model_load(self):
        try:
            self.engine = PDFSearchEngine(progress_callback=self._update_progress)
            self.root.after(0, self.model_load_complete, True, None)
        except Exception as e:
            self.root.after(0, self.model_load_complete, False, str(e))

    def model_load_complete(self, success, error_msg):
        self._hide_progress()
        if success:
            self.file_lbl.configure(text="✅ AI engines online. Ready for PDF.", text_color="#00ff9d")
            self.set_ui_state("normal")
            self.status_bar.configure(text="✅ Sentence Transformer & Cross-Encoder loaded")
        else:
            self.file_lbl.configure(text="❌ Engine Initialization Failed.", text_color="#ff4757")
            messagebox.showerror("Fatal Error", f"AI pipeline failed to load:\n\n{error_msg}")

    def start_file_loading(self):
        if self.is_processing:
            return
        if self.ocr_mode and not self._check_ocr_ready():
            messagebox.showwarning("OCR Not Ready", "OCR engine not installed.\nClick OCR MODE to install it first.")
            return
        file_path = filedialog.askopenfilename(title="Select PDF Document", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.selected_file_path = file_path
            mode_name = "OCR" if self.ocr_mode else "Normal"
            self.file_lbl.configure(text=f"⏳ Selected: {os.path.basename(file_path)} — Preparing ({mode_name})...", text_color="#ffd166")
            self.set_ui_state("disabled")
            self.settings_btn.configure(state="disabled")
            self._show_progress(f"Preparing {mode_name} extraction...")
            self.is_processing = True
            threading.Thread(target=self.async_file_index, args=(file_path,), daemon=True).start()

    def async_file_index(self, file_path):
        try:
            self.engine.load_and_index_pdf(file_path, progress_callback=self._update_progress, use_ocr=self.ocr_mode)
            self.root.after(0, self.file_index_complete, True, None)
        except Exception as e:
            self.root.after(0, self.file_index_complete, False, str(e))

    def file_index_complete(self, success, error_message):
        self.is_processing = False
        self._hide_progress()
        self.set_ui_state("normal")
        self.settings_btn.configure(state="normal")
        if success:
            mode_text = "OCR" if self.ocr_mode else "Normal"
            self.file_lbl.configure(text=f"📄 {os.path.basename(self.selected_file_path)} ({len(self.engine.sentences):,} chunks) [{mode_text}]", text_color="#00ff9d")
            self.status_bar.configure(text="✅ Document indexed and semantic tensors loaded")
            messagebox.showinfo("Indexing Complete", f"Successfully structured into {len(self.engine.sentences):,} cross-referenced chunks.")
        else:
            self.file_lbl.configure(text="❌ Indexing failed.", text_color="#ff4757")
            self.status_bar.configure(text="❌ Process Failed")
            messagebox.showerror("Document Error", f"An error occurred:\n\n{error_message}")

    def trigger_search(self):
        if not self.engine or not self.engine.sentences:
            messagebox.showwarning("Search Blocked", "Please index a valid PDF document first.")
            return
        query = self.query_entry.get().strip()
        if not query:
            return
        self.set_ui_state("disabled")
        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0", "🔍 Analyzing semantic patterns and sorting vectors...")
        self.status_bar.configure(text="🔍 Searching...")
        self.root.update()
        threading.Thread(target=self.async_search, args=(query,), daemon=True).start()

    def async_search(self, query):
        try:
            answer, score = self.engine.search(query)
            self.root.after(0, self.search_complete, answer, score)
        except Exception as e:
            self.root.after(0, self.search_complete, f"Search error:\n{str(e)}", 0.0)

    def search_complete(self, answer, score):
        self.set_ui_state("normal")
        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0", f"🎯 TOP RETRIEVAL MATCH\n")
        self.output_text.insert("end", f"Confidence: {score:.2f}%\n")
        self.output_text.insert("end", "─" * 50 + "\n\n")
        self.output_text.insert("end", answer)
        self.status_bar.configure(text=f"✅ Search complete — Confidence: {score:.1f}%")

    def open_settings(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("⚙️ Settings")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="Appearance", font=("Segoe UI", 16, "bold")).pack(pady=20)
        theme_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        theme_frame.pack(pady=10)
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=10)
        theme_var = ctk.StringVar(value=self.settings.get("theme", "dark"))
        ctk.CTkOptionMenu(theme_frame, values=["dark", "light"], variable=theme_var).pack(side="left")
        def save():
            self.settings["theme"] = theme_var.get()
            ctk.set_appearance_mode(self.settings["theme"])
            save_settings(self.settings)
            dialog.destroy()
        ctk.CTkButton(dialog, text="Apply", command=save).pack(pady=20)

if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFSearchApp(root)
    root.mainloop()
