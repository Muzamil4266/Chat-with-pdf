# ChatWithPDF 📄🚀

ChatWithPDF is a high-performance, fully local desktop application built in Python that allows users to have intelligent conversations with their PDF documents. By combining lexical and semantic search engines, the application delivers incredibly accurate, context-aware answers to user queries completely offline.

Equipped with an advanced OCR pipeline and a modern graphical interface, ChatWithPDF easily handles both digital text-based PDFs and scanned document images.

---

## 📋 Table of Contents
- [What is ChatWithPDF?](#-what-is-chatwithpdf)
- [Key Features](#-key-features)
- [Technical Stack](#-technical-stack)
- [How it Works (Architecture)](#-how-it-works-architecture)
- [Installation & Setup](#-installation--setup)
  - [Method 1: Running from Source (Development)](#method-1-running-from-source-development)
  - [Method 2: Building the Production Installer](#method-2-building-the-production-installer)
- [How to Use](#-how-to-use)
- [Applications & Use Cases](#-applications--use-cases)

---

## 🔍 What is ChatWithPDF?

Unlike standard search features that rely on exact keyword matching, ChatWithPDF acts as a localized **Retrieval-Augmented Generation (RAG)** pipeline. It ingests your documents, breaks them into logical fragments, indexes them using advanced search algorithms, and retrieves the exact paragraph or sentence needed to answer your question. 

Because it runs completely on your local machine, your sensitive documents are never uploaded to the cloud, ensuring total data privacy.

---

## ✨ Key Features

*   **Hybrid Search Engine:** Combines **BM25 (lexical/keyword search)** with **Dense Semantic Embeddings** to catch both exact terms and deep contextual meanings.
*   **Built-in OCR Pipeline:** Seamlessly reads scanned images, historical documents, and low-quality PDFs using an embedded OCR engine.
*   **Modern GUI:** A clean, dark-mode responsive interface built entirely with CustomTkinter.
*   **Zero-Lag Performance:** Local configurations, model weights, and user settings are cached efficiently within the Windows user profile directory (`AppData/Local`) to eliminate runtime overhead.
*   **Completely Offline:** No API keys, no internet connection required after initial setup, and zero cloud data leakage.

---

## 🛠️ Technical Stack

*   **GUI Framework:** `customtkinter` (Modern, dark-theme wrapper for Tkinter)
*   **PDF Parsing Engine:** `PyMuPDF (fitz)` & `pdfplumber` (High-speed document structure parsing)
*   **Text Processing:** `numpy` & `PIL (Pillow)`
*   **OCR Engine:** `easyocr` powered by `torch` and `torchvision`
*   **Information Retrieval:** 
    *   Lexical: `rank_bm25`
    *   Semantic: `sentence_transformers` (BERT-based embedding representations)

---

## 🏗️ How it Works (Architecture)

1.  **Ingestion:** The user loads a PDF file through the CustomTkinter GUI.
2.  **Extraction:** `PyMuPDF` extracts native text. If a page contains non-selectable image text, `EasyOCR` automatically triggers to transcribe the text layer.
3.  **Chunking & Indexing:** Text content is split into optimized semantic chunks. These chunks are dual-indexed using a local `BM25` matrix and a `SentenceTransformer` vector space.
4.  **Querying:** When you type a question, the application cross-references both indices, scores the relevance mathematically, and surfaces the best matching context from the document instantly.

---

## 📦 Installation & Setup

### Method 1: Running from Source (Development)

To set up the project locally for development, follow these steps:

1. **Clone the repository:**
```bash
   git clone [https://github.com/yourusername/chat-with-pdf.git](https://github.com/yourusername/chat-with-pdf.git)
   cd chat-with-pdf
