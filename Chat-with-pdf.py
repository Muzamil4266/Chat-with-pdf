# ================================================================================
# PYINSTALLER BUILD COMMAND (run in terminal):
# pyinstaller --noconfirm --onefile --windowed --name "ChatWithPDF" ^
#   --add-data "hub;hub" --add-data "easyocr_models;easyocr_models" ^
#   --hidden-import fitz --hidden-import PyMuPDF --hidden-import pdfplumber ^
#   --hidden-import rank_bm25 --hidden-import sentence_transformers ^
#   --hidden-import customtkinter --hidden-import easyocr --hidden-import PIL ^
#   --hidden-import numpy --hidden-import torch --hidden-import torchvision ^
#   --hidden-import tkinter --hidden-import tkinter.filedialog ^
#   --collect-all customtkinter --collect-all sentence_transformers --collect-all easyocr ^
#   "FINAL .py"
# ================================================================================
"""
app.py - Complete Chat With PDF Application
OFFLINE BUNDLED VERSION - No internet required
"""

import os
import sys

# ========================================================================
# OFFLINE MODE: Always use local hub folder, never download from internet
# ========================================================================
# PyInstaller fix: when frozen, use EXE directory; when script, use script directory
# ========================================================================
# FIXED OFFLINE PATH RESOLUTION: Target internal extraction folder (_MEIPASS)
# ========================================================================
# ========================================================================
# FIXED OFFLINE PATH RESOLUTION: Target internal extraction folder (_MEIPASS)
# ========================================================================
if getattr(sys, 'frozen', False):
    # This points inside the heavy EXE where everything extracts at runtime
    _bundle_dir = sys._MEIPASS 
    # This points outside to the user's actual folder (for saving settings/cache)
    _user_dir = os.path.dirname(sys.executable)
else:
    _bundle_dir = os.path.dirname(os.path.abspath(__file__))
    _user_dir = _bundle_dir

# Point huggingface and easyocr to internal bundled folders inside the heavy EXE
os.environ["HF_HOME"] = _bundle_dir
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(_bundle_dir, "hub")
os.environ["EASYOCR_MODULE_PATH"] = os.path.join(_bundle_dir, "easyocr_models")
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"

# Disable all online features
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# TensorFlow/PyTorch quiet mode
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import subprocess
import importlib
import gc
import tempfile
import atexit

import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger().setLevel(logging.ERROR)

# ========================================================================
# AUTO-INSTALLER: Skipped in offline mode - all packages must be pre-installed
# ========================================================================
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "pdfplumber": "pdfplumber",
    "rank_bm25": "rank-bm25",
    "sentence_transformers": "sentence-transformers",
    "numpy": "numpy",
    "PIL": "pillow",
    "fitz": "pymupdf",
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

def show_installer_gui(missing_packages):
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Installing Dependencies")
    root.geometry("500x250")
    root.configure(bg="#0a0a1a")
    root.resizable(False, False)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"+{(screen_w-500)//2}+{(screen_h-250)//2}")

    tk.Label(root, text="Installing Required Packages", font=("Segoe UI", 16, "bold"),
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
            status_lbl.config(text="Installation complete! Launching app...", fg="#00ff9d")
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


# ========================================================================
# CHECK & INSTALL: Skipped in offline mode - all packages must be pre-installed
# ========================================================================
# OFFLINE: Auto-installer disabled. Install packages manually:
#   pip install customtkinter pdfplumber rank-bm25 sentence-transformers numpy pillow pymupdf easyocr
#   pip install torch --index-url https://download.pytorch.org/whl/cpu
# If you get ImportError, install the missing package manually.

# missing = check_and_install_packages()
# if missing:
#     print(f"Missing packages: {[p[1] for p in missing]}")
#     print("Launching installer GUI...")
#     show_installer_gui(missing)
#     still_missing = check_and_install_packages()
#     if still_missing:
#         print(f"Still missing: {[p[1] for p in still_missing]}")
#         sys.exit(1)

# ========================================================================
# NOW IMPORT EVERYTHING
# ========================================================================
import re
import threading
import io
import time
import numpy as np
import json
import shutil
import hashlib
import webbrowser

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pdfplumber
from rank_bm25 import BM25Okapi

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# FIX #39, #40, #41: Restore stderr properly with try/finally
_stderr_backup = sys.stderr
try:
    sys.stderr = io.StringIO()
    from sentence_transformers import SentenceTransformer, CrossEncoder, util
finally:
    sys.stderr = _stderr_backup

# EasyOCR for OCR (replaces Tesseract)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Save settings and cache safely in User Profile AppData to prevent Windows permission errors
_appdata_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ChatWithPDF")
os.makedirs(_appdata_dir, exist_ok=True)

SETTINGS_FILE = os.path.join(_appdata_dir, "pdf_app_settings.json")
MAX_PAGES = 5000
CACHE_DIR = os.path.join(_appdata_dir, "pdf_cache")
MAX_CACHE_SIZE_GB = 2.0
MAX_RECENT_PDFS = 15
QUICK_MODE_PAGES = 200
STREAMING_BATCH_SIZE = 50

DEFAULT_SETTINGS = {
    "theme": "dark",
    "accent_color": "#ff0040",
    "ocr_mode": False,
    "font_family": "Segoe UI",
    "font_size": 12,
    "quick_mode": False,
    "results_count": 5,
    "result_box_height": 150,
    "result_card_padx": 10,
    "result_card_pady": 5,
}

os.makedirs(CACHE_DIR, exist_ok=True)

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


def get_cache_size():
    total = 0
    for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total / (1024**3)


def cleanup_old_cache():
    while get_cache_size() > MAX_CACHE_SIZE_GB:
        files = []
        for f in os.listdir(CACHE_DIR):
            if f.endswith('.json'):
                path = os.path.join(CACHE_DIR, f)
                files.append((path, os.path.getatime(path)))
        if not files:
            break
        files.sort(key=lambda x: x[1])
        oldest = files[0][0]
        base = oldest[:-5]
        for ext in ['.json', '.npy', '_sentences.npy', '_embeddings.npy', '_bm25.npy', 
                    '_page_map.npy', '_tokenized.npy', '_meta.json']:
            fpath = base + ext
            if os.path.exists(fpath):
                os.remove(fpath)


def get_pdf_fingerprint(pdf_path):
    """Compute SHA-256 hash of file content for truly content-based caching."""
    sha256 = hashlib.sha256()
    try:
        with open(pdf_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
    except (OSError, IOError):
        stat = os.stat(pdf_path)
        size = stat.st_size
        mtime = stat.st_mtime
        key_string = f"{pdf_path}|{size}|{mtime}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    return sha256.hexdigest()


def save_pdf_cache(pdf_path, sentences, embeddings, page_map, tokenized_corpus, 
                   chunks_count, total_pages, file_size_mb):
    cleanup_old_cache()
    pdf_hash = get_pdf_fingerprint(pdf_path)
    cache_base = os.path.join(CACHE_DIR, pdf_hash)
    temp_base = cache_base + ".tmp"

    cache_data = {
        "pdf_path": pdf_path,
        "pdf_name": os.path.basename(pdf_path),
        "chunks_count": chunks_count,
        "total_pages": total_pages,
        "file_size_mb": file_size_mb,
        "page_map": page_map,
        "timestamp": time.time(),
        "fully_indexed": True,
    }

    try:
        with open(temp_base + '.json', 'w') as f:
            json.dump(cache_data, f)
        np.save(temp_base + '_sentences.npy', np.array(sentences, dtype=object))
        np.save(temp_base + '_embeddings.npy', embeddings)
        np.save(temp_base + '_bm25.npy', np.array(tokenized_corpus, dtype=object))

        for ext in ['.json', '_sentences.npy', '_embeddings.npy', '_bm25.npy']:
            src = temp_base + ext
            dst = cache_base + ext
            if os.path.exists(src):
                os.replace(src, dst)
    except Exception:
        for ext in ['.json', '_sentences.npy', '_embeddings.npy', '_bm25.npy']:
            src = temp_base + ext
            if os.path.exists(src):
                os.remove(src)
        raise


def load_pdf_cache(pdf_path):
    pdf_hash = get_pdf_fingerprint(pdf_path)
    cache_base = os.path.join(CACHE_DIR, pdf_hash)

    json_path = cache_base + '.json'
    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, 'r') as f:
            cache_data = json.load(f)

        sentences = np.load(cache_base + '_sentences.npy', allow_pickle=True).tolist()
        embeddings = np.load(cache_base + '_embeddings.npy')
        page_map = cache_data.get('page_map', [])
        tokenized_corpus = np.load(cache_base + '_bm25.npy', allow_pickle=True).tolist() if os.path.exists(cache_base + '_bm25.npy') else None

        if len(sentences) != embeddings.shape[0]:
            raise ValueError(f"Cache corrupt: sentences ({len(sentences)}) != embeddings ({embeddings.shape[0]})")

        return {
            'sentences': sentences,
            'embeddings': embeddings,
            'page_map': page_map,
            'tokenized_corpus': tokenized_corpus,
            'chunks_count': cache_data.get('chunks_count', 0),
            'total_pages': cache_data.get('total_pages', 0),
            'fully_indexed': cache_data.get('fully_indexed', False),
        }
    except Exception as e:
        delete_pdf_cache(pdf_hash)
        return None


def get_recent_pdfs():
    recent = []
    for f in os.listdir(CACHE_DIR):
        if f.endswith('.json') and not f.endswith('.tmp.json'):
            path = os.path.join(CACHE_DIR, f)
            try:
                with open(path, 'r') as fp:
                    data = json.load(fp)
                if data.get('fully_indexed', False):
                    recent.append(data)
            except:
                pass
    recent.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return recent[:MAX_RECENT_PDFS]


def delete_pdf_cache(pdf_hash):
    cache_base = os.path.join(CACHE_DIR, pdf_hash)
    for ext in ['.json', '.tmp.json', '_sentences.npy', '_embeddings.npy', '_bm25.npy',
                '_page_map.npy', '_tokenized.npy', '_meta.json']:
        fpath = cache_base + ext
        if os.path.exists(fpath):
            os.remove(fpath)


# ========================================================================
# AI SEARCH ENGINE - CORE ENGINES UNCHANGED
# ========================================================================
class PDFSearchEngine:
    def __init__(self, progress_callback=None, cancel_flag=None):
        self.progress_callback = progress_callback
        self.cancel_flag = cancel_flag
        self._safe_progress("Loading Retrieval Model (Sentence Transformer)...", 5)

        _stderr_backup = sys.stderr
        try:
            sys.stderr = io.StringIO()
            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"
            self.retrieval_model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
        finally:
            sys.stderr = _stderr_backup

        self._safe_progress("Loading Cross-Encoder (Re-ranker)...", 60)
        _stderr_backup = sys.stderr
        try:
            sys.stderr = io.StringIO()
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        finally:
            sys.stderr = _stderr_backup

        self._safe_progress("AI Engines Ready!", 100)
        self.sentences = []
        self.embeddings = None
        self.bm25 = None
        self.page_map = []
        self.tokenized_corpus = []
        self.is_cancelled = False
        self.models_loaded = True
        self.partial_index_ready = False
        self.total_pages_processed = 0
        self._search_lock = threading.Lock()
        self._query_cache = {}
        self._page_char_offsets = []
        self._easyocr_reader = None  # Will be initialized when needed

    def _safe_progress(self, msg, pct):
        if self.progress_callback:
            try:
                self.progress_callback(msg, pct)
            except Exception as e:
                logging.warning(f"Progress callback error: {e}")

    def _check_cancelled(self):
        if self.cancel_flag and self.cancel_flag.is_set():
            self.is_cancelled = True
            raise InterruptedError("Indexing cancelled by user.")

    def reuse_engine_data(self, cached_data):
        if self.embeddings is not None:
            del self.embeddings
            self.embeddings = None
        gc.collect()

        self.sentences = cached_data['sentences']
        self.embeddings = cached_data['embeddings']
        self.page_map = cached_data['page_map']
        self.tokenized_corpus = cached_data.get('tokenized_corpus', [])
        self.total_pages_processed = cached_data.get('total_pages', 0)

        if self.tokenized_corpus and len(self.tokenized_corpus) == len(self.sentences):
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.tokenized_corpus = [doc.lower().split() for doc in self.sentences]
            self.bm25 = BM25Okapi(self.tokenized_corpus)

        self._rebuild_char_offsets()
        self.partial_index_ready = True
        self._query_cache.clear()

    def _rebuild_char_offsets(self):
        self._page_char_offsets = []
        total = 0
        for text, page in self.page_map:
            length = len(text)
            self._page_char_offsets.append((total, total + length, page))
            total += length

    def _find_page_for_sentence(self, sentence_idx):
        if not self._page_char_offsets:
            return 1

        target_char = sum(len(s) for s in self.sentences[:sentence_idx])

        lo, hi = 0, len(self._page_char_offsets)
        while lo < hi:
            mid = (lo + hi) // 2
            start, end, page = self._page_char_offsets[mid]
            if target_char < start:
                hi = mid
            elif target_char >= end:
                lo = mid + 1
            else:
                return page

        return self._page_char_offsets[-1][2] if self._page_char_offsets else 1

    def _init_easyocr(self):
        """Initialize EasyOCR reader (lazy loading)"""
        if self._easyocr_reader is None:
            if not EASYOCR_AVAILABLE:
                raise ImportError("EasyOCR not installed. Run: pip install easyocr")
            # Debug: verify model path (remove after testing if desired)
            print(f"[EasyOCR] Model path: {os.environ.get('EASYOCR_MODULE_PATH', 'NOT SET')}")
            self._safe_progress("Loading EasyOCR engine (first time may take a moment)...", 10)
            # Force EasyOCR to use the internal bundled models and strictly disable internet downloading
            self._easyocr_reader = easyocr.Reader(
                ['en'], 
                gpu=False, 
                verbose=False, 
                model_storage_directory=os.environ.get('EASYOCR_MODULE_PATH'),
                download_enabled=False
               )

    def load_and_index_pdf(self, file_path, progress_callback=None, use_ocr=False, 
                           quick_mode=False, cancel_flag=None, streaming_callback=None):
        self.progress_callback = progress_callback
        self.cancel_flag = cancel_flag
        self.is_cancelled = False
        self.partial_index_ready = False

        page_limit = QUICK_MODE_PAGES if quick_mode else MAX_PAGES

        if use_ocr and EASYOCR_AVAILABLE:
            text, page_map = self._ocr_extract(file_path, progress_callback, page_limit)
        elif use_ocr and not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR not installed. Run: pip install easyocr")
        else:
            text, page_map = self._normal_extract(file_path, progress_callback, page_limit)

        self._check_cancelled()

        if not text or len(text.strip()) < 50:
            raise ValueError("No extractable text found. Try OCR mode for scanned PDFs.")

        if progress_callback:
            progress_callback("Cleaning text...", 52)
        text = self._clean_extracted_text(text)

        self._check_cancelled()

        if progress_callback:
            progress_callback("Splitting sentences...", 55)

        raw_sentences = self._smart_sentence_split(text)
        raw_sentences = [s.strip() for s in raw_sentences if len(s.strip().split()) >= 3]

        self.sentences = []
        for i in range(len(raw_sentences) - 1):
            combined = f"{raw_sentences[i]} {raw_sentences[i+1]}"
            combined = re.sub(r'\s+', ' ', combined)
            self.sentences.append(combined)
        if not self.sentences:
            self.sentences = raw_sentences
        if not self.sentences:
            raise ValueError("No extractable text found in this PDF.")

        self.sentences = self._deduplicate_sentences(self.sentences)
        chunks_count = len(self.sentences)

        if progress_callback:
            progress_callback(f"Building keyword index... {chunks_count:,} chunks created", 60)

        self._check_cancelled()

        self.tokenized_corpus = [doc.lower().split() for doc in self.sentences]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        self.page_map = page_map
        self.total_pages_processed = len(page_map)

        self._rebuild_char_offsets()

        embeddings_list = []
        batch_size = 32
        total = len(self.sentences)

        for batch_num in range(0, total, batch_size):
            self._check_cancelled()
            batch = self.sentences[batch_num:batch_num + batch_size]
            batch_emb = self.retrieval_model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_emb)

            if streaming_callback and batch_num >= STREAMING_BATCH_SIZE:
                partial_emb = np.vstack(embeddings_list)
                self.embeddings = partial_emb
                self.partial_index_ready = True
                streaming_callback(f"Partial index ready: {batch_num + len(batch):,} / {total:,} chunks searchable", 
                                  65 + int((batch_num + len(batch)) / total * 35))

            if progress_callback:
                current = min(batch_num + batch_size, total)
                pct = 65 + int(current / total * 35)
                progress_callback(f"Encoding chunk {current:,} / {total:,}", pct)

        self.embeddings = np.vstack(embeddings_list)
        self.partial_index_ready = True
        self._query_cache.clear()

        if progress_callback:
            progress_callback(f"Indexing complete! {chunks_count:,} chunks ready", 100)

        return chunks_count, len(page_map)

    def _smart_sentence_split(self, text):
        abbreviations = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.', 'St.', 
                        'Ave.', 'Blvd.', 'Rd.', 'No.', 'Vol.', 'Inc.', 'Ltd.', 'Jr.',
                        'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'U.S.', 'U.K.', 'E.U.', 'U.N.',
                        'i.e.', 'e.g.', 'et al.', 'etc.', 'vs.', 'vol.', 'fig.', 'Fig.']

        protected_text = text
        placeholders = {}
        placeholder_id = 0

        for abbrev in abbreviations:
            pattern = re.escape(abbrev)
            for match in re.finditer(pattern, protected_text):
                placeholder = f"<ABBR{placeholder_id}>"
                placeholders[placeholder] = match.group()
                protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
                placeholder_id += 1

        raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected_text)

        result = []
        for sent in raw:
            for placeholder, original in placeholders.items():
                sent = sent.replace(placeholder, original)
            result.append(sent)

        return result

    def _deduplicate_sentences(self, sentences):
        seen = set()
        unique = []
        for sent in sentences:
            normalized = re.sub(r'\s+', ' ', sent.lower().strip())
            if normalized not in seen or len(normalized) > 100:
                seen.add(normalized)
                unique.append(sent)
            elif len(normalized) <= 100:
                pass
        return unique

    def _clean_extracted_text(self, text):
        """FIXED: Proper text cleaning that preserves word boundaries."""
        # Replace actual whitespace characters first
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Collapse multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)

        # Add space between camelCase (e.g., "AnneFrank" -> "Anne Frank")
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        # Fix words that got merged without space (e.g., "howas" -> "how as")
        # This is a common OCR issue - words merge when spaces are lost
        # We use a dictionary-based approach or pattern matching
        # For now, we rely on the sentence splitter to handle this

        # Remove zero-width spaces and other invisible characters
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)

        return text.strip()

    def _normal_extract(self, file_path, progress_callback=None, page_limit=MAX_PAGES):
        text = ""
        page_map = []
        with pdfplumber.open(file_path) as pdf:
            total_pages = min(len(pdf.pages), page_limit)
            for i in range(total_pages):
                self._check_cancelled()
                page = pdf.pages[i]
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + " "
                    page_map.append((page_text + " ", i + 1))
                if progress_callback:
                    pct = int((i + 1) / total_pages * 50)
                    progress_callback(f"Reading PDF... Page {i+1}/{total_pages} ({pct}%)", pct)
        if progress_callback:
            progress_callback(f"Extracted {total_pages} pages (50%)", 50)
        return text, page_map

    def _ocr_extract(self, file_path, progress_callback=None, page_limit=MAX_PAGES):
        """OCR using EasyOCR - works on almost all PDFs"""
        
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR not installed. Run: pip install easyocr")
        
        # Initialize EasyOCR (lazy loading)
        self._init_easyocr()
        
        actual_limit = min(page_limit, MAX_PAGES)
        
        if progress_callback:
            progress_callback("Converting PDF to images using PyMuPDF...", 20)
        
        # Use PyMuPDF (fitz) to convert PDF to images
        import fitz
        doc = fitz.open(file_path)
        total_pages = min(len(doc), actual_limit)
        
        text = ""
        page_map = []
        
        for page_num in range(total_pages):
            self._check_cancelled()
            
            # Convert page to image
            page = doc[page_num]
            zoom = 2.0  # 144 DPI (good for OCR)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_data))
            
            if progress_callback:
                pct = 20 + int((page_num + 1) / total_pages * 60)
                progress_callback(f"OCR scanning page {page_num + 1}/{total_pages}...", pct)
            
            # Run EasyOCR
            try:
                import numpy as np
                result = self._easyocr_reader.readtext(np.array(img), detail=0, paragraph=True)
                page_text = " ".join(result)
                
                if page_text and page_text.strip():
                    text += page_text + " "
                    page_map.append((page_text + " ", page_num + 1))
            except Exception as e:
                print(f"OCR warning on page {page_num + 1}: {e}")
            
            img.close()
        
        doc.close()
        
        if progress_callback:
            progress_callback("Processing complete...", 100)
        
        if not text or len(text.strip()) < 50:
            raise ValueError("No extractable text found even with OCR. The PDF may be empty, corrupted, or image-only with very poor quality.")
        
        return text, page_map

    def search(self, user_query, cancel_flag=None):
        with self._search_lock:
            if not self.sentences or self.embeddings is None:
                return [{"text": "Engine not ready. Please index a PDF first.", "score": 0.0, "page": 1}]

            if cancel_flag and cancel_flag.is_set():
                return [{"text": "Search cancelled.", "score": 0.0, "page": 1}]

            cache_key = hashlib.sha256(user_query.lower().strip().encode()).hexdigest()[:16]
            if cache_key in self._query_cache:
                query_emb = self._query_cache[cache_key]
            else:
                query_emb = self.retrieval_model.encode([user_query], show_progress_bar=False)
                self._query_cache[cache_key] = query_emb

            vector_scores = util.cos_sim(query_emb, self.embeddings).cpu().numpy().ravel()

            top_k = 5
            top_vector_idx = np.argpartition(vector_scores, -top_k)[-top_k:]
            top_vector_idx = top_vector_idx[np.argsort(vector_scores[top_vector_idx])[::-1]]

            query_lower = user_query.lower().split()
            bm25_scores = self.bm25.get_scores(query_lower)
            top_keyword_idx = np.argpartition(bm25_scores, -top_k)[-top_k:]
            top_keyword_idx = top_keyword_idx[np.argsort(bm25_scores[top_keyword_idx])[::-1]]

            candidate_indices = list(set(list(top_vector_idx) + list(top_keyword_idx)))
            top_n = min(5, len(candidate_indices))

            if not candidate_indices:
                return [{"text": "No relevant matches found.", "score": 0.0, "page": 1}]

            pairs = [[user_query, self.sentences[idx]] for idx in candidate_indices]

            try:
                cross_scores = self.reranker.predict(pairs)
            except Exception as e:
                logging.warning(f"Cross-encoder failed, falling back to vector scores: {e}")
                cross_scores = vector_scores[candidate_indices]

            cross_scores = np.clip(cross_scores, -20, 20)
            final_scores = 1 / (1 + np.exp(-cross_scores)) * 100

            if len(final_scores) != len(candidate_indices):
                logging.error(f"Score mismatch: {len(final_scores)} scores for {len(candidate_indices)} candidates")
                final_scores = np.ones(len(candidate_indices)) * 50.0

            best_indices = np.argpartition(final_scores, -top_n)[-top_n:]
            best_indices = best_indices[np.argsort(final_scores[best_indices])[::-1]]

            results = []
            for idx in best_indices:
                global_idx = candidate_indices[idx]
                page_num = self._find_page_for_sentence(global_idx)
                results.append({
                    "text": self.sentences[global_idx],
                    "score": float(final_scores[idx]),
                    "page": page_num
                })
            return results


# ========================================================================
# FRONTEND - CUSTOMTKINTER MAIN APP
# ========================================================================

from PIL import Image as PILImage, ImageTk

class PDFSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat With PDF")
        self.root.geometry("1500x1000")
        self.root.minsize(1300, 900)
        
        self.settings = load_settings()
        
        # Apply theme immediately
        theme = self.settings.get("theme", "dark")
        if theme == "dark":
            ctk.set_appearance_mode("dark")
        elif theme == "light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")  # red/purple use dark mode
        ctk.set_default_color_theme("dark-blue")
        
        self.engine = None
        self.selected_file_path = None
        self.ocr_mode = self.settings.get("ocr_mode", False)
        self.quick_mode = self.settings.get("quick_mode", False)
        self.is_processing = False
        self.query_history = []
        self.cancel_flag = threading.Event()
        self.current_results = []
        self._recent_dialog = None
        self._model_loading = False
        self._temp_images = []

        self._font_family = self.settings.get("font_family", "Segoe UI")
        self._font_size = self.settings.get("font_size", 12)
        
        # Apply font to customtkinter
        ctk.FontManager.load_font(self._font_family)

        self.build_ui()
        
        # Apply accent color after UI is built
        self.apply_accent_color(self.settings.get("accent_color", "#ff0040"))
        
        # Apply theme background if red or purple
        self.apply_theme_background(theme)
        
        self.root.after(500, self.start_model_loading)

        import atexit
        atexit.register(self._cleanup_temp_images)
    def start_loading_animation(self):
        self.loading_animation_running = True
        self.animate_loading_bar()

    def stop_loading_animation(self):
        self.loading_animation_running = False

    def animate_loading_bar(self):
        if not self.loading_animation_running:
            return

        width = self.loading_canvas.winfo_width()

        current = getattr(self, "_loading_pos", 0)
        current += 12

        if current > width:
            current = -250

        self._loading_pos = current

        self.loading_canvas.coords(
            self.loading_bar,
            current,
            8,
            current + 250,
            32
        )

        self.root.after(25, self.animate_loading_bar)
    def apply_theme_background(self, theme):
        """Apply theme-specific background colors"""
        if theme == "red":
            self.root.configure(fg_color="#1a0000")
            if hasattr(self, 'main_frame'):
                self.main_frame.configure(fg_color="transparent")
        elif theme == "purple":
            self.root.configure(fg_color="#1a001a")
            if hasattr(self, 'main_frame'):
                self.main_frame.configure(fg_color="transparent")
        else:
            self.root.configure(fg_color=("#e8e8f0" if theme == "light" else "#0a0a1a"))

    def apply_accent_color(self, color):
        """Apply accent color to all UI elements"""
        self.accent_color = color
        # Update progress bar
        if hasattr(self, 'progress_bar'):
            self.progress_bar.configure(progress_color=color)
        # Update cancel button
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(fg_color=color, hover_color="#cc0033")
        # Update mode buttons based on current mode
        self.update_mode_buttons()
        # Update search button
        if hasattr(self, 'search_btn'):
            self.search_btn.configure(fg_color=color, hover_color="#cc0033")

    def _apply_fonts_to_ui(self):
        """Dynamically apply font family and size to all UI widgets."""
        self._font_family = self.settings.get("font_family", "Segoe UI")
        self._font_size = self.settings.get("font_size", 12)

        # Update header labels
        for widget in [self.file_lbl, self.progress_lbl, self.progress_title, 
                       self.progress_pct_lbl, self.mode_indicator, self.streaming_lbl,
                       self.status_bar]:
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(font=(self._font_family, self._font_size))
                except:
                    pass

        # Update entry
        if hasattr(self, 'query_entry'):
            try:
                self.query_entry.configure(font=(self._font_family, self._font_size + 1))
            except:
                pass

        # Update buttons
        for btn in [self.file_btn, self.search_btn, self.recent_btn, self.settings_btn,
                    self.normal_btn, self.ocr_btn, self.export_btn, self.cancel_btn,
                    self.clear_history_btn]:
            if hasattr(btn, 'configure'):
                try:
                    btn.configure(font=(self._font_family, self._font_size - 1, "bold"))
                except:
                    pass

    def _cleanup_temp_images(self):
        """Remove all temporary page images on exit."""
        for img_path in self._temp_images:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except:
                pass
        self._temp_images.clear()

    

    def build_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # === HEADER ===
        header = ctk.CTkFrame(self.main_frame, fg_color="#1a0a1a", corner_radius=15)
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Chat With PDF", font=(self._font_family, self._font_size + 12, "bold"), text_color="#ff0040").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(header, text="AI-Powered PDF Analysis", font=(self._font_family, self._font_size, "bold"), text_color="#b04bff").pack(side="left", padx=5)

        self.recent_btn = ctk.CTkButton(header, text="Recent PDFs", font=(self._font_family, self._font_size - 1, "bold"), 
                                        width=120, height=40, corner_radius=10, fg_color="#2a0a2a", 
                                        hover_color="#4a0a4a", command=self.show_recent_pdfs)
        self.recent_btn.pack(side="right", padx=5)

        self.settings_btn = ctk.CTkButton(header, text="⚙️", width=40, height=40, corner_radius=10, 
                                          fg_color="#2a0a2a", hover_color="#4a0a4a", command=self.open_settings)
        self.settings_btn.pack(side="right", padx=15)

        # === QUICK MODE TOGGLE ===
        quick_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=10)
        quick_frame.pack(fill="x", pady=(0, 10))
        self.quick_var = ctk.BooleanVar(value=self.quick_mode)
        self.quick_switch = ctk.CTkSwitch(quick_frame, text="Quick Mode (First 200 pages only)", 
                                          variable=self.quick_var, command=self.toggle_quick_mode,
                                          font=(self._font_family, self._font_size - 1), text_color="#ffd166")
        self.quick_switch.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(quick_frame, text="Useful for huge textbooks. Full indexing available after.", 
                     font=(self._font_family, self._font_size - 2), text_color="#6a6a9e").pack(side="left", padx=5)

        # === HISTORY DROPDOWN ===
        history_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=10)
        history_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(history_frame, text="History:", font=(self._font_family, self._font_size - 1), text_color="#b04bff").pack(side="left", padx=15)
        self.history_var = ctk.StringVar(value="Select previous query...")
        self.history_dropdown = ctk.CTkOptionMenu(history_frame, values=["Select previous query..."], 
                                                    variable=self.history_var, command=self._on_history_select,
                                                    width=400, font=(self._font_family, self._font_size - 2))
        self.history_dropdown.pack(side="left", padx=10, pady=5)

        self.clear_history_btn = ctk.CTkButton(history_frame, text="Clear", font=(self._font_family, self._font_size - 2),
                                               width=60, height=28, corner_radius=8, fg_color="#2a0a2a",
                                               hover_color="#4a0a4a", command=self._clear_history)
        self.clear_history_btn.pack(side="left", padx=5)

        # === EXTRACTION MODE ===
        mode_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        mode_card.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(mode_card, text="EXTRACTION MODE", font=(self._font_family, self._font_size, "bold"), text_color="#ff0040").pack(anchor="w", padx=15, pady=(10, 5))
        btn_frame = ctk.CTkFrame(mode_card, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=15, pady=5)
        self.normal_btn = ctk.CTkButton(btn_frame, text="NORMAL", font=(self._font_family, self._font_size, "bold"), width=140, height=40, corner_radius=10, command=lambda: self.set_mode(False))
        self.normal_btn.pack(side="left", padx=(0, 10))
        self.ocr_btn = ctk.CTkButton(btn_frame, text="OCR", font=(self._font_family, self._font_size, "bold"), width=140, height=40, corner_radius=10, fg_color="#2a0a2a", hover_color="#4a0a4a", command=lambda: self.set_mode(True))
        self.ocr_btn.pack(side="left")
        ctk.CTkLabel(mode_card, text="Normal: Best for text-based PDFs  |  OCR: Use for scanned documents\nAsk matching questions for accurate results  |  Relevance score shown after each answer",
                     font=(self._font_family, self._font_size - 2), text_color="#b04bff", justify="left").pack(anchor="w", padx=15, pady=(5, 10))

        # === DOCUMENT CARD ===
        doc_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        doc_card.pack(fill="x", pady=(0, 10))
        doc_inner = ctk.CTkFrame(doc_card, fg_color="transparent")
        doc_inner.pack(fill="x", padx=15, pady=8)
        self.file_btn = ctk.CTkButton(doc_inner, text="SELECT PDF", font=(self._font_family, self._font_size + 1, "bold"), width=180, height=32, corner_radius=12, command=self.start_file_loading)
        self.file_btn.pack(side="left")
        self.file_lbl = ctk.CTkLabel(doc_inner, text="Initializing AI engines...", font=(self._font_family, self._font_size, "bold"), text_color="#b04bff")
        self.file_lbl.pack(side="left", fill="x", expand=True, padx=(20, 10))

        # === PROGRESS CARD ===
        self.progress_card = ctk.CTkFrame(self.main_frame, fg_color="#0d0a0d", corner_radius=15)
        # Don't pack yet - will show when needed
        
        self.progress_title = ctk.CTkLabel(self.progress_card, text="📄 PROCESSING PDF", font=(self._font_family, self._font_size + 2, "bold"), text_color="#ff0040")
        self.progress_title.pack(anchor="center", pady=(15, 5))
        
        self.progress_lbl = ctk.CTkLabel(self.progress_card, text="Ready", font=(self._font_family, self._font_size + 1), text_color="#e8e8f0")
        self.progress_lbl.pack(anchor="center", pady=(0, 10))

        self.progress_pct_lbl = ctk.CTkLabel(self.progress_card, text="0%", font=(self._font_family, 32, "bold"), text_color="#ff0040")
        self.progress_pct_lbl.pack(anchor="center", pady=(5, 5))
        self.loading_canvas = tk.Canvas(
            self.progress_card,
            height=40,
            bg="#0d0a0d",
            highlightthickness=0,
            bd=0
        )
        self.loading_canvas.pack(fill="x", padx=40, pady=(0, 10))

        self.loading_bar = self.loading_canvas.create_rectangle(
            0, 10, 0, 30,
            fill="#00ffff",
            outline=""
        )

        self.loading_animation_running = False
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_card,
            width=1000,
            height=24,
            corner_radius=20,
            progress_color="#00e5ff",
            fg_color="#08131a"
        )
        self.progress_bar.pack(fill="x", padx=30, pady=(10, 15))
        self.progress_bar.set(0)

        self.cancel_btn = ctk.CTkButton(self.progress_card, text="✕ CANCEL PROCESSING", font=(self._font_family, self._font_size, "bold"), 
                                        width=160, height=40, corner_radius=10, fg_color="#ff0040", 
                                        hover_color="#cc0033", command=self.cancel_indexing)
        self.cancel_btn.pack(anchor="center", pady=(0, 10))

        # === SEARCH CARD ===
        search_card = ctk.CTkFrame(self.main_frame, fg_color="#1e0a1e", corner_radius=15)
        search_card.pack(fill="x", pady=(0, 10))
        search_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=8)
        self.mode_indicator = ctk.CTkLabel(search_inner, text="MODE: NORMAL (Standard Document Parsing)", font=(self._font_family, self._font_size - 1, "bold"), text_color="#00ff9d")
        self.mode_indicator.pack(anchor="w", pady=(0, 0))

        self.streaming_lbl = ctk.CTkLabel(search_inner, text="", font=(self._font_family, self._font_size - 2), text_color="#ffd166")
        self.streaming_lbl.pack(anchor="w", pady=(0, 0))

        query_frame = ctk.CTkFrame(search_inner, fg_color="transparent")
        
        query_frame.pack(fill="x", pady=(0, 0))

        self.query_entry = ctk.CTkEntry(query_frame, font=(self._font_family, self._font_size + 1), height=35, corner_radius=10, 
                                       placeholder_text="Ask a question about your PDF...", 
                                       border_color="#4a0a4a", border_width=2)
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.trigger_search())
        self.query_entry.bind("<Control-Return>", lambda e: self.trigger_search())

        self.search_btn = ctk.CTkButton(query_frame, text="SEARCH", font=(self._font_family, self._font_size, "bold"), width=120, height=45, corner_radius=10, command=self.trigger_search)
        self.search_btn.pack(side="right")
        self.export_btn = ctk.CTkButton(query_frame, text="Export", font=(self._font_family, self._font_size - 1), width=80, height=45, corner_radius=10, fg_color="#2a0a2a", hover_color="#4a0a4a", command=self.export_results)
        self.export_btn.pack(side="right", padx=(0, 10))

        # === RESULTS AREA ===
        output_card = ctk.CTkFrame(self.main_frame, fg_color="#050505", corner_radius=15)
        output_card.pack(fill="both", expand=True, pady=(0, 0))
        output_card.lift()
        self.results_frame_parent = output_card

        output_header = ctk.CTkFrame(output_card, fg_color="transparent")
        output_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            output_header,
            text="📋 SEARCH RESULTS",
            font=(self._font_family, self._font_size, "bold"),
            text_color="#ff0040"
        ).pack(side="left")

        self.results_frame = ctk.CTkScrollableFrame(
            output_card,
            fg_color="#050505",
            corner_radius=10
        )

        self.results_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )
        self.status_bar = ctk.CTkLabel(self.main_frame, text="Ready", font=(self._font_family, self._font_size - 2), 
                                      text_color="#b04bff", wraplength=1050)
        self.status_bar.pack(fill="x", pady=(10, 0))
        self.update_mode_buttons()

    def _show_progress(self, message="Initializing..."):
        # Hide first if already visible
        self.progress_card.pack_forget()
        # Pack before results area
        self.progress_card.pack(fill="x", pady=(0, 10), before=self.results_frame_parent)
        self.progress_title.configure(text="📄 " + (message.split()[0] if message else "PROCESSING"))
        self.progress_lbl.configure(text=message)
        self.progress_pct_lbl.configure(text="0%")
        self.progress_bar.set(0)
        self.root.update()

    def _hide_progress(self):
        self.progress_card.pack_forget()
        self.root.update()

    def _update_progress(self, message, percentage):
        self.progress_lbl.configure(text=message)
        self.progress_bar.set(percentage / 100.0)
        self.progress_pct_lbl.configure(text=f"{percentage}%")
        
        if percentage < 30:
            stage_emoji = "📄"
            stage_text = "LOADING PDF"
        elif percentage < 60:
            stage_emoji = "🔍"
            stage_text = "EXTRACTING TEXT"
        elif percentage < 90:
            stage_emoji = "🧠"
            stage_text = "BUILDING INDEX"
        else:
            stage_emoji = "✅"
            stage_text = "FINALIZING"
        
        self.progress_title.configure(text=f"{stage_emoji} {stage_text} {stage_emoji}")
        
        display_msg = message[:80] + "..." if len(message) > 80 else message
        self.status_bar.configure(text=f"{display_msg}")
        self.root.update()

    def cancel_indexing(self):
        self.cancel_flag.set()
        self.status_bar.configure(text="Cancelling...")

    def toggle_quick_mode(self):
        self.quick_mode = self.quick_var.get()
        self.settings["quick_mode"] = self.quick_mode
        save_settings(self.settings)
        if self.quick_mode:
            self.status_bar.configure(text="Quick Mode enabled: First 200 pages only")
        else:
            self.status_bar.configure(text="Full Mode: All pages will be indexed")

    def update_mode_buttons(self):
        accent = self.accent_color if hasattr(self, 'accent_color') else self.settings.get("accent_color", "#ff0040")
        if self.ocr_mode:
            self.ocr_btn.configure(fg_color=accent, text_color="#0a0a1a", hover_color="#cc0033")
            self.normal_btn.configure(fg_color="#2a0a2a", text_color="#e8e8f0", hover_color="#4a0a4a")
            self.mode_indicator.configure(text="MODE: OCR (Scanned PDFs - EasyOCR)", text_color="#ffd166")
        else:
            self.normal_btn.configure(fg_color=accent, text_color="#0a0a1a", hover_color="#cc0033")
            self.ocr_btn.configure(fg_color="#2a0a2a", text_color="#e8e8f0", hover_color="#4a0a4a")
            self.mode_indicator.configure(text="MODE: NORMAL (Standard Document Parsing)", text_color="#00ff9d")

    def set_mode(self, use_ocr):
        if use_ocr:
            if EASYOCR_AVAILABLE:
                self.ocr_mode = True
                self.settings["ocr_mode"] = True
                save_settings(self.settings)
                self.update_mode_buttons()
                self.status_bar.configure(text="OCR mode enabled. EasyOCR ready (works on scanned documents).")
                return
            else:
                self.status_bar.configure(text="EasyOCR not installed. Run: pip install easyocr")
                self.ocr_mode = False
                self.settings["ocr_mode"] = False
                save_settings(self.settings)
                self.update_mode_buttons()
                messagebox.showinfo("OCR Setup Required", 
                    "EasyOCR is not installed.\n\n"
                    "Run this command in terminal:\n"
                    "pip install easyocr\n\n"
                    "This will install EasyOCR (modern OCR engine) and all dependencies.")
        else:
            self.ocr_mode = False
            self.settings["ocr_mode"] = False
            save_settings(self.settings)
            self.update_mode_buttons()
            self.status_bar.configure(text="Normal mode enabled.")

    def set_ui_state(self, state):
        states = {"normal": "normal", "disabled": "disabled"}
        widget_state = states.get(state, state)
        self.file_btn.configure(state=widget_state)
        self.search_btn.configure(state=widget_state)
        self.query_entry.configure(state=widget_state)
        self.normal_btn.configure(state=widget_state)
        self.ocr_btn.configure(state=widget_state)
        self.recent_btn.configure(state=widget_state)
        self.settings_btn.configure(state=widget_state)
        self.clear_history_btn.configure(state=widget_state)

    def start_model_loading(self):
        self._model_loading = True
        self._show_progress("Loading AI engines from local storage...")
        self.progress_bar.set(0.05)
        threading.Thread(target=self.async_model_load, daemon=True).start()

    def async_model_load(self):
        try:
            self.engine = PDFSearchEngine(progress_callback=self._update_progress)
            self.root.after(0, self.model_load_complete, True, None)
        except Exception as e:
            self.root.after(0, self.model_load_complete, False, str(e))
        finally:
            self._model_loading = False

    def model_load_complete(self, success, error_msg):
        self._hide_progress()
        if success:
            self.file_lbl.configure(text="AI engines online. Ready for PDF.", text_color="#00ff9d")
            self.set_ui_state("normal")
            self.status_bar.configure(text="Sentence Transformer & Cross-Encoder loaded (offline mode)")
        else:
            self.file_lbl.configure(text="Engine Initialization Failed.", text_color="#ff4757")
            messagebox.showerror("Fatal Error", f"AI pipeline failed to load:\n{error_msg}")

    def start_file_loading(self):
        if self.is_processing:
            return
        file_path = filedialog.askopenfilename(title="Select PDF Document", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.selected_file_path = file_path
            self.cancel_flag.clear()
            self.is_cancelled = False

            self.query_history.clear()
            self._update_history_dropdown()

            mode_name = "OCR" if self.ocr_mode else "Normal"
            quick_text = " (Quick Mode: 200 pages)" if self.quick_mode else ""
            self.file_lbl.configure(text=f"Selected: {os.path.basename(file_path)} - Preparing ({mode_name}{quick_text})...", text_color="#ffd166")
            self.set_ui_state("disabled")
            self._show_progress(f"Preparing {mode_name} extraction...")
            self.start_loading_animation()
            self.is_processing = True
            threading.Thread(target=self.async_file_index, args=(file_path,), daemon=True).start()

    def async_file_index(self, file_path):
        try:
            cached = load_pdf_cache(file_path)
            if cached and cached.get('fully_indexed', False):
                self.root.after(0, self.file_index_complete_cached, cached)
                return

            if self.engine and self.engine.models_loaded:
                pass
            else:
                self.engine = PDFSearchEngine(progress_callback=self._update_progress, cancel_flag=self.cancel_flag)

            def streaming_callback(msg, pct):
                self.root.after(0, lambda: self.streaming_lbl.configure(text=f"{msg}"))
                self.root.after(0, lambda: self.status_bar.configure(text=f"{msg[:80]}..." if len(msg) > 80 else f"{msg}"))

            chunks_count, pages_processed = self.engine.load_and_index_pdf(
                file_path, 
                progress_callback=self._update_progress, 
                use_ocr=self.ocr_mode,
                quick_mode=self.quick_mode,
                cancel_flag=self.cancel_flag,
                streaming_callback=streaming_callback
            )

            if self.engine.is_cancelled:
                self.root.after(0, self.file_index_cancelled)
                return

            file_size_mb = os.path.getsize(file_path) / (1024**2)
            total_pages = pages_processed

            save_pdf_cache(file_path, self.engine.sentences, self.engine.embeddings, 
                          self.engine.page_map, self.engine.tokenized_corpus,
                          chunks_count, total_pages, file_size_mb)

            self.root.after(0, self.file_index_complete, True, None, chunks_count, total_pages, file_size_mb)
        except InterruptedError:
            self.root.after(0, self.file_index_cancelled)
        except Exception as e:
            self.root.after(0, self.file_index_complete, False, str(e), 0, 0, 0)

    def file_index_complete_cached(self, cached_data):
        self.stop_loading_animation()
        if self._model_loading:
            self.root.after(100, lambda: self.file_index_complete_cached(cached_data))
            return

        self.is_processing = False
        self._hide_progress()
        self.set_ui_state("normal")

        if self.engine and self.engine.models_loaded:
            self.engine.reuse_engine_data(cached_data)
        else:
            self.engine = PDFSearchEngine()
            self.engine.reuse_engine_data(cached_data)

        self.file_lbl.configure(
            text=f"{os.path.basename(self.selected_file_path)} ({cached_data['chunks_count']:,} chunks) [CACHED - Ready instantly]", 
            text_color="#00ff9d"
        )
        self.status_bar.configure(text="Loaded from cache in 1 second. No re-indexing.")
        self.streaming_lbl.configure(text="Full document ready for search")

    def file_index_cancelled(self):
        self.stop_loading_animation()
        self.is_processing = False
        self._hide_progress()
        self.set_ui_state("normal")
        self.file_lbl.configure(text="Indexing cancelled by user.", text_color="#ff4757")
        self.status_bar.configure(text="Cancelled. Partial results not saved to Recent PDFs.")
        self.streaming_lbl.configure(text="")

    def file_index_complete(self, success, error_message, chunks_count, total_pages, file_size_mb):
        self.stop_loading_animation()
        self.is_processing = False
        self._hide_progress()
        self.set_ui_state("normal")
        if success:
            mode_text = "OCR" if self.ocr_mode else "Normal"
            quick_text = " [QUICK MODE]" if self.quick_mode else ""
            self.file_lbl.configure(
                text=f"{os.path.basename(self.selected_file_path)} ({chunks_count:,} chunks) [{mode_text}{quick_text}]", 
                text_color="#00ff9d"
            )
            self.status_bar.configure(text=f"Document indexed: {chunks_count:,} chunks from {total_pages} pages")
            self.streaming_lbl.configure(text=f"Full document ready for search | Size: {file_size_mb:.1f} MB")
            messagebox.showinfo("Indexing Complete", f"Successfully structured into {chunks_count:,} cross-referenced chunks.\nTotal pages: {total_pages}")
        else:
            self.file_lbl.configure(text="Indexing failed.", text_color="#ff4757")
            self.status_bar.configure(text="Process Failed")
            messagebox.showerror("Document Error", f"An error occurred:\n{error_message}")
            self.streaming_lbl.configure(text="")

    def trigger_search(self):
        if not self.engine or not self.engine.sentences:
            messagebox.showwarning("Search Blocked", "Please index a valid PDF document first.")
            return

        query = self.query_entry.get().strip()
        query = re.sub(r'[\t\n\r]+', ' ', query).strip()

        if len(query) > 500:
            messagebox.showwarning("Query Too Long", "Query must be under 500 characters.")
            return

        if not query:
            return

        self.set_ui_state("disabled")

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.status_bar.configure(text="Searching...")
        self.root.update()
        threading.Thread(target=self.async_search, args=(query,), daemon=True).start()

    def async_search(self, query):
        try:
            results = self.engine.search(query, cancel_flag=self.cancel_flag)
            self.root.after(0, self.search_complete, query, results)
        except Exception as e:
            self.root.after(0, self.search_complete, query, [{"text": f"Search error:\n{str(e)}", "score": 0.0, "page": 1}])

    def search_complete(self, query, results):
        try:
            self.set_ui_state("normal")
            self.current_results = results

            self.query_history.append((query, results))
            self._update_history_dropdown()

            for widget in self.results_frame.winfo_children():
                widget.destroy()

            header = ctk.CTkLabel(self.results_frame, text=f'📊 Results for: "{query}"', 
                                 font=(self._font_family, self._font_size + 2, "bold"), text_color="#ff0040")
            header.pack(anchor="w", pady=(0, 5))

            max_results = self.settings.get("results_count", 5)
            results = results[:max_results]

            box_h = self.settings.get("result_box_height", 150)
            card_px = self.settings.get("result_card_padx", 10)
            card_py = self.settings.get("result_card_pady", 5)

            for i, result in enumerate(results, 1):
                card = ctk.CTkFrame(self.results_frame, fg_color="#1a0a1a", corner_radius=12, border_color="#4a0a4a", border_width=2)
                card.pack(fill="x", pady=card_py, padx=card_px)

                text_content = result['text']

                # === SINGLE HORIZONTAL TOP BAR ===
                top_bar = ctk.CTkFrame(card, fg_color="transparent")
                top_bar.pack(fill="x", padx=15, pady=(8, 2))

                ctk.CTkLabel(top_bar, text=f"🔹 #{i}",
                            font=(self._font_family, self._font_size, "bold"), text_color="#00ff9d").pack(side="left")

                ctk.CTkLabel(top_bar, text=f"🎯 {result['score']:.1f}%",
                            font=(self._font_family, self._font_size - 1), text_color="#b04bff").pack(side="left", padx=(6, 0))

                ctk.CTkLabel(top_bar, text=f"📄 P{result['page']}",
                            font=(self._font_family, self._font_size - 1), text_color="#ffd166").pack(side="left", padx=(6, 0))

                ctk.CTkButton(top_bar, text="📖 Open", font=(self._font_family, self._font_size - 2, "bold"),
                              width=70, height=22, corner_radius=6, fg_color="#2a0a2a",
                              hover_color="#4a0a4a",
                              command=lambda p=result['page']: self.open_pdf_at_page(p)).pack(side="left", padx=(8, 4))

                ctk.CTkButton(top_bar, text="💾 Save", font=(self._font_family, self._font_size - 2, "bold"),
                              width=60, height=22, corner_radius=6, fg_color=self.accent_color if hasattr(self, 'accent_color') else "#ff0040",
                              hover_color="#cc0033",
                              command=lambda q=query, r=result: self.save_bookmark(q, r)).pack(side="left", padx=4)

                ctk.CTkButton(top_bar, text="📋 Copy", font=(self._font_family, self._font_size - 2, "bold"),
                              width=55, height=22, corner_radius=6, fg_color="#2a0a2a",
                              hover_color="#4a0a4a",
                              command=lambda t=text_content: self._copy_to_clipboard(t)).pack(side="left", padx=4)

                text_height = max(60, min(box_h, len(text_content) // 8))

                text_box = ctk.CTkTextbox(card, height=text_height, font=(self._font_family, self._font_size + 1), wrap="word",
                                         fg_color="#0d0a0d", text_color="#e8e8f0", corner_radius=10, border_width=1, border_color="#4a0a4a")
                text_box.pack(fill="x", padx=15, pady=(0, 5))
                text_box.insert("1.0", text_content)
                text_box.configure(state="disabled")

            self.status_bar.configure(text=f"Search complete - {len(results)} matches found")

            try:
                self.results_frame._parent_canvas.yview_moveto(0)
            except:
                pass
        except Exception as e:
            self.set_ui_state("normal")
            self.status_bar.configure(text=f"Search display error: {str(e)}")
            messagebox.showerror("Search Error", f"Failed to display results:\n{str(e)}")                

    def _copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_bar.configure(text="Text copied to clipboard")

    def _clear_history(self):
        self.query_history.clear()
        self._update_history_dropdown()
        self.status_bar.configure(text="History cleared")

    def open_pdf_at_page(self, page_num):
        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            messagebox.showwarning("PDF Not Found", "The PDF file is no longer available.")
            return

        try:
            if PYMUPDF_AVAILABLE:
                self._show_page_image(page_num)
                return

            if sys.platform == 'win32':
                adobe_paths = [
                    r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                    r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                ]
                for adobe in adobe_paths:
                    if os.path.exists(adobe):
                        subprocess.Popen([adobe, '/A', f'page={page_num}', self.selected_file_path])
                        self.status_bar.configure(text=f"Opened PDF at Page {page_num} (Adobe Reader)")
                        return

                sumatra_paths = [
                    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                ]
                for sumatra in sumatra_paths:
                    if os.path.exists(sumatra):
                        subprocess.Popen([sumatra, '-page', str(page_num), self.selected_file_path])
                        self.status_bar.configure(text=f"Opened PDF at Page {page_num} (SumatraPDF)")
                        return

                os.startfile(self.selected_file_path)
                self.status_bar.configure(text=f"Opened PDF (navigate to Page {page_num} manually)")
                messagebox.showinfo("Navigation Tip", f"PDF opened. Please navigate to Page {page_num} manually.")

            elif sys.platform == 'darwin':
                subprocess.call(['open', self.selected_file_path])
                self.status_bar.configure(text=f"Opened PDF (navigate to Page {page_num} manually)")
                messagebox.showinfo("Navigation Tip", f"PDF opened. Please navigate to Page {page_num} manually.")

            else:
                subprocess.call(['xdg-open', self.selected_file_path])
                self.status_bar.configure(text=f"Opened PDF (navigate to Page {page_num} manually)")
                messagebox.showinfo("Navigation Tip", f"PDF opened. Please navigate to Page {page_num} manually.")

        except Exception as e:
            messagebox.showerror("Open Failed", f"Could not open PDF:\n{str(e)}")

    def _show_page_image(self, page_num):
        if not PYMUPDF_AVAILABLE:
            messagebox.showerror("PDF Viewer", "PyMuPDF not available for image rendering.")
            return

        try:
            doc = fitz.open(self.selected_file_path)
            if page_num < 1 or page_num > len(doc):
                messagebox.showwarning("Invalid Page", f"Page {page_num} is out of range.")
                doc.close()
                return

            page = doc[page_num - 1]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)

            temp_img = os.path.join(CACHE_DIR, f"page_{page_num}_{int(time.time())}.png")
            pix.save(temp_img)
            doc.close()

            self._temp_images.append(temp_img)

            popup = ctk.CTkToplevel(self.root)
            popup.title(f"Page {page_num} - {os.path.basename(self.selected_file_path)}")
            popup.geometry("800x900")
            popup.transient(self.root)

            try:
                img = PILImage.open(temp_img)
                w, h = img.size
                max_w, max_h = 750, 800
                if w > max_w or h > max_h:
                    ratio = min(max_w/w, max_h/h)
                    new_w, new_h = int(w*ratio), int(h*ratio)
                    img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)

                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                popup._img_ref = ctk_img

                img_label = ctk.CTkLabel(popup, image=ctk_img, text="")
                img_label.pack(pady=20)

                ctk.CTkLabel(popup, text=f"Page {page_num} of {os.path.basename(self.selected_file_path)}",
                            font=(self._font_family, self._font_size, "bold"), text_color="#e8e8f0").pack(pady=10)

                def cleanup_and_close():
                    try:
                        if os.path.exists(temp_img):
                            os.remove(temp_img)
                        if temp_img in self._temp_images:
                            self._temp_images.remove(temp_img)
                    except:
                        pass
                    popup.destroy()

                ctk.CTkButton(popup, text="Close", command=cleanup_and_close,
                             font=(self._font_family, self._font_size - 1), fg_color=self.accent_color if hasattr(self, 'accent_color') else "#ff0040",
                             hover_color="#cc0033").pack(pady=10)

                self.status_bar.configure(text=f"Showing Page {page_num} as image")

            except Exception as img_e:
                messagebox.showerror("Image Display Failed", f"Could not display image:\n{str(img_e)}")
                popup.destroy()

        except Exception as e:
            messagebox.showerror("Image Render Failed", f"Could not render page:\n{str(e)}")

    def save_bookmark(self, query, result):
        if not self.selected_file_path:
            return

        bookmark = {
            "pdf": os.path.basename(self.selected_file_path),
            "pdf_path": self.selected_file_path,
            "page": result['page'],
            "query": query,
            "answer": result['text'],
            "score": round(result['score'], 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        bookmarks_file = "pdf_bookmarks.json"
        bookmarks = []
        if os.path.exists(bookmarks_file):
            try:
                with open(bookmarks_file, 'r') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        bookmarks = loaded
            except (json.JSONDecodeError, ValueError):
                bookmarks = []

        bookmark_key = f"{bookmark['pdf']}|{bookmark['page']}|{bookmark['query']}"
        existing_keys = [f"{b['pdf']}|{b['page']}|{b['query']}" for b in bookmarks]

        if bookmark_key not in existing_keys:
            bookmarks.append(bookmark)

            if len(bookmarks) > 1000:
                bookmarks = bookmarks[-1000:]

            with open(bookmarks_file, 'w') as f:
                json.dump(bookmarks, f, indent=2)

            self.status_bar.configure(text=f"Bookmark saved: {query[:30]}... (Page {result['page']})")
            messagebox.showinfo("Bookmark Saved", f"Saved to pdf_bookmarks.json\nPage {result['page']}: {query}")
        else:
            self.status_bar.configure(text=f"Bookmark already exists for this query+page")
            messagebox.showinfo("Bookmark Exists", "This bookmark already exists.")

    def _update_history_dropdown(self):
        if not self.query_history:
            self.history_dropdown.configure(values=["Select previous query..."])
            return
        queries = ["Select previous query..."] + [q for q, r in self.query_history[-10:]]
        self.history_dropdown.configure(values=queries)

    def _on_history_select(self, choice):
        if choice == "Select previous query...":
            return
        self.query_entry.delete(0, "end")
        self.query_entry.insert(0, choice)
        self.trigger_search()

    def show_recent_pdfs(self):
        if self._recent_dialog is not None and self._recent_dialog.winfo_exists():
            self._recent_dialog.lift()
            return

        recent = get_recent_pdfs()

        self._recent_dialog = ctk.CTkToplevel(self.root)
        dialog = self._recent_dialog
        dialog.title("Recent PDFs")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()

        def close_dialog():
            dialog.destroy()
            self._recent_dialog = None

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

        ctk.CTkLabel(dialog, text="Recent PDFs", font=(self._font_family, self._font_size + 8, "bold"), text_color="#ff0040").pack(pady=20)
        ctk.CTkLabel(dialog, text="Click any PDF to load instantly. Only fully indexed PDFs appear here.", 
                     font=(self._font_family, self._font_size - 1), text_color="#b04bff").pack(pady=(0, 10))

        close_btn = ctk.CTkButton(dialog, text="Close", command=close_dialog,
                                   font=(self._font_family, self._font_size - 1), fg_color="#2a0a2a",
                                   hover_color="#4a0a4a", width=80, height=30)
        close_btn.pack(pady=(0, 10))

        scroll_frame = ctk.CTkScrollableFrame(dialog, width=450, height=400)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        if not recent:
            ctk.CTkLabel(scroll_frame, text="No recent PDFs found.\nProcess a PDF fully to see it here.", 
                        font=(self._font_family, self._font_size), text_color="#6a6a9e").pack(pady=50)
        else:
            for pdf_data in recent:
                card = ctk.CTkFrame(scroll_frame, fg_color="#1e0a1e", corner_radius=12)
                card.pack(fill="x", pady=8, padx=5)

                ctk.CTkLabel(card, text=f"{pdf_data['pdf_name']}", 
                            font=(self._font_family, self._font_size + 1, "bold"), text_color="#e8e8f0").pack(anchor="w", padx=15, pady=(10, 2))

                info_text = f"   100% Indexed\n   {pdf_data['chunks_count']:,} Chunks\n   {pdf_data['file_size_mb']:.1f} MB\n   {pdf_data['total_pages']} Pages"
                ctk.CTkLabel(card, text=info_text, font=(self._font_family, self._font_size - 2), 
                            text_color="#6a6a9e", justify="left").pack(anchor="w", padx=15, pady=(2, 10))

                for widget in [card] + list(card.winfo_children()):
                    widget.bind("<Button-1>", lambda e, p=pdf_data['pdf_path']: self.load_recent_pdf(p, dialog))

    def load_recent_pdf(self, pdf_path, dialog):
        if self._model_loading:
            messagebox.showinfo("Please Wait", "AI engines are still loading. Please wait a moment.")
            return

        if not os.path.exists(pdf_path):
            messagebox.showerror("File Not Found", "The PDF file has been moved or deleted.")
            return

        dialog.destroy()
        self._recent_dialog = None
        self.selected_file_path = pdf_path
        self.file_lbl.configure(text=f"Loading {os.path.basename(pdf_path)} from cache...", text_color="#ffd166")
        self.root.update()

        self.query_history.clear()
        self._update_history_dropdown()

        cached = load_pdf_cache(pdf_path)
        if cached:
            if self.engine and self.engine.models_loaded:
                self.engine.reuse_engine_data(cached)
            else:
                self.engine = PDFSearchEngine()
                self.engine.reuse_engine_data(cached)

            self.file_lbl.configure(
                text=f"{os.path.basename(pdf_path)} ({cached['chunks_count']:,} chunks) [CACHED - Ready]", 
                text_color="#00ff9d"
            )
            self.status_bar.configure(text="Loaded from cache in 1 second. No re-indexing.")
            self.streaming_lbl.configure(text="Full document ready for search")
        else:
            messagebox.showerror("Cache Error", "Could not load from cache. Please re-index the PDF.")

    def export_results(self):
        if not self.query_history:
            messagebox.showinfo("No Results", "No search results to export yet.")
            return

        pdf_name = os.path.basename(self.selected_file_path) if self.selected_file_path else "Unknown"
        if not self.selected_file_path:
            if not messagebox.askyesno("No PDF Selected", "No PDF is currently selected. Export anyway?"):
                return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Search Results"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("CHAT WITH PDF - SEARCH RESULTS\n")
                    f.write(f"Document: {pdf_name}\n")
                    f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")

                    for idx, (query, results) in enumerate(self.query_history, 1):
                        f.write(f"QUERY #{idx}: {query}\n")
                        f.write("-" * 40 + "\n")
                        for r in results:
                            f.write(f"  Page {r['page']} | Score: {r['score']:.1f}%\n")
                            f.write(f"  {r['text']}\n\n")
                        f.write("\n")

                messagebox.showinfo("Exported", f"Saved {len(self.query_history)} queries to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def open_settings(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("520x850")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Appearance Settings", font=(self._font_family, self._font_size + 6, "bold")).pack(pady=20)

        # Theme selection
        theme_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        theme_frame.pack(pady=10)
        ctk.CTkLabel(theme_frame, text="Theme:", font=(self._font_family, self._font_size)).pack(side="left", padx=10)
        theme_var = ctk.StringVar(value=self.settings.get("theme", "dark"))
        theme_options = ["dark", "light", "red", "purple"]
        theme_display = ["Dark", "Light", "Red", "Purple"]

        current_display = theme_display[theme_options.index(theme_var.get())]
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=theme_display, 
                                        variable=ctk.StringVar(value=current_display),
                                        font=(self._font_family, self._font_size - 1))
        theme_menu.pack(side="left")

        def get_theme_value(display_name):
            mapping = {"Dark": "dark", "Light": "light", "Red": "red", "Purple": "purple"}
            return mapping.get(display_name, "dark")

        def on_theme_change(display_choice):
            theme_var.set(get_theme_value(display_choice))

        theme_menu.configure(command=on_theme_change)

        # Accent Color
        ctk.CTkLabel(dialog, text="Accent Color", font=(self._font_family, self._font_size + 2, "bold")).pack(pady=(20, 5))
        accent_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        accent_frame.pack(pady=5)

        accent_colors = ["#ff0040", "#00ff9d", "#00d4ff", "#ffd166", "#b04bff", "#ff0000", "#800080", "#ff6600"]
        accent_var = ctk.StringVar(value=self.settings.get("accent_color", "#ff0040"))

        color_btn_frame = ctk.CTkFrame(accent_frame, fg_color="transparent")
        color_btn_frame.pack(pady=5)

        for color in accent_colors:
            btn = ctk.CTkButton(color_btn_frame, text="", width=45, height=35, corner_radius=8,
                               fg_color=color, hover_color=color,
                               command=lambda c=color: accent_var.set(c))
            btn.pack(side="left", padx=3)

        accent_preview = ctk.CTkLabel(accent_frame, text=f"Selected: {accent_var.get()}", 
                                      font=(self._font_family, self._font_size - 1), text_color="#b04bff")
        accent_preview.pack(pady=5)

        def update_accent_preview(*args):
            accent_preview.configure(text=f"Selected: {accent_var.get()}")
        accent_var.trace('w', update_accent_preview)

        # Font Family
        ctk.CTkLabel(dialog, text="Font Family", font=(self._font_family, self._font_size + 2, "bold")).pack(pady=(20, 5))
        font_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        font_frame.pack(pady=5)
        font_var = ctk.StringVar(value=self.settings.get("font_family", "Segoe UI"))
        font_options = ["Segoe UI", "Arial", "Helvetica", "Times New Roman", "Verdana", "Calibri", "Tahoma"]
        font_menu = ctk.CTkOptionMenu(font_frame, values=font_options, variable=font_var, 
                                      width=250, font=(self._font_family, self._font_size - 1))
        font_menu.pack()

        # Font Size
        ctk.CTkLabel(dialog, text="Font Size", font=(self._font_family, self._font_size + 2, "bold")).pack(pady=(20, 5))
        size_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        size_frame.pack(pady=5)
        size_var = ctk.IntVar(value=self.settings.get("font_size", 12))

        def update_font_size_label(value):
            size_label.configure(text=f"{int(float(value))}px")

        size_slider = ctk.CTkSlider(size_frame, from_=10, to=20, number_of_steps=10,
                                    variable=size_var, command=update_font_size_label,
                                    width=250, height=15)
        size_slider.pack()
        size_label = ctk.CTkLabel(size_frame, text=f"{size_var.get()}px", font=(self._font_family, self._font_size))
        size_label.pack(pady=5)

        # === SEARCH RESULTS LAYOUT ===
        ctk.CTkLabel(dialog, text="Search Results Layout", font=(self._font_family, self._font_size + 2, "bold")).pack(pady=(20, 5))

        layout_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        layout_frame.pack(pady=5, padx=20)

        # Number of results
        ctk.CTkLabel(layout_frame, text="Results shown:", font=(self._font_family, self._font_size)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        results_menu = ctk.CTkOptionMenu(layout_frame, values=["1", "2", "3", "4", "5"],
                                        width=80, font=(self._font_family, self._font_size - 1))
        results_menu.set(str(self.settings.get("results_count", 5)))
        results_menu.grid(row=0, column=1, padx=5, pady=5)

        # Result box height
        ctk.CTkLabel(layout_frame, text="Text box height:", font=(self._font_family, self._font_size)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        box_height_label = ctk.CTkLabel(layout_frame, text=f"{self.settings.get('result_box_height', 150)}px", font=(self._font_family, self._font_size - 1))
        box_height_label.grid(row=1, column=2, padx=5, pady=5)
        box_slider = ctk.CTkSlider(layout_frame, from_=60, to=300, number_of_steps=24,
                                    command=lambda v: box_height_label.configure(text=f"{int(float(v))}px"),
                                    width=150, height=15)
        box_slider.set(self.settings.get("result_box_height", 150))
        box_slider.grid(row=1, column=1, padx=5, pady=5)

        # Card spacing X
        ctk.CTkLabel(layout_frame, text="Card spacing X:", font=(self._font_family, self._font_size)).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        padx_label = ctk.CTkLabel(layout_frame, text=f"{self.settings.get('result_card_padx', 10)}px", font=(self._font_family, self._font_size - 1))
        padx_label.grid(row=2, column=2, padx=5, pady=5)
        padx_slider = ctk.CTkSlider(layout_frame, from_=0, to=40, number_of_steps=8,
                                   command=lambda v: padx_label.configure(text=f"{int(float(v))}px"),
                                   width=150, height=15)
        padx_slider.set(self.settings.get("result_card_padx", 10))
        padx_slider.grid(row=2, column=1, padx=5, pady=5)

        # Card spacing Y
        ctk.CTkLabel(layout_frame, text="Card spacing Y:", font=(self._font_family, self._font_size)).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        pady_label = ctk.CTkLabel(layout_frame, text=f"{self.settings.get('result_card_pady', 5)}px", font=(self._font_family, self._font_size - 1))
        pady_label.grid(row=3, column=2, padx=5, pady=5)
        pady_slider = ctk.CTkSlider(layout_frame, from_=0, to=30, number_of_steps=6,
                                   command=lambda v: pady_label.configure(text=f"{int(float(v))}px"),
                                   width=150, height=15)
        pady_slider.set(self.settings.get("result_card_pady", 5))
        pady_slider.grid(row=3, column=1, padx=5, pady=5)

        def save():
            try:
                # Save all settings
                self.settings["theme"] = theme_var.get()
                self.settings["accent_color"] = accent_var.get()
                self.settings["font_family"] = font_var.get()
                self.settings["font_size"] = int(size_var.get())
                self.settings["results_count"] = int(results_menu.get())
                self.settings["result_box_height"] = int(box_slider.get())
                self.settings["result_card_padx"] = int(padx_slider.get())
                self.settings["result_card_pady"] = int(pady_slider.get())

                # Apply theme appearance mode
                theme = self.settings["theme"]
                if theme == "dark":
                    ctk.set_appearance_mode("dark")
                elif theme == "light":
                    ctk.set_appearance_mode("light")
                else:
                    ctk.set_appearance_mode("dark")

                # Apply accent color to UI elements
                self.accent_color = self.settings["accent_color"]
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.configure(progress_color=self.accent_color)
                if hasattr(self, 'cancel_btn'):
                    self.cancel_btn.configure(fg_color=self.accent_color)
                if hasattr(self, 'search_btn'):
                    self.search_btn.configure(fg_color=self.accent_color)
                self.update_mode_buttons()

                # Apply fonts dynamically to all existing widgets
                self._apply_fonts_to_ui()

                # Save to file
                save_settings(self.settings)

                messagebox.showinfo("Settings Saved", "All settings applied instantly.\nTheme, colors, fonts, and layout updated.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Settings Error", f"Failed to save settings:\n{str(e)}")
                import traceback
                traceback.print_exc()

        ctk.CTkButton(dialog, text="Apply Settings", command=save, 
                     font=(self._font_family, self._font_size, "bold"),
                     fg_color=self.accent_color if hasattr(self, 'accent_color') else self.settings.get("accent_color", "#ff0040"),
                     hover_color="#cc0033", width=160, height=45, corner_radius=10).pack(pady=30)

    def _refresh_theme(self):
        if self.ocr_mode:
            self.mode_indicator.configure(text_color="#ffd166")
        else:
            self.mode_indicator.configure(text_color="#00ff9d")
        self.status_bar.configure(text="Theme updated. Restart for full effect.")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFSearchApp(root)
    root.mainloop()
