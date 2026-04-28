# Async Document Processor 📄⚡

An asynchronous document processing API built with FastAPI. This service allows users to upload PDF documents (like invoices), extracts the text in the background, and uses Groq's **Llama-3.3-70b-versatile** model to classify the document and extract structured JSON data.

## Features

- **Asynchronous Processing:** Returns a `job_id` instantly while processing the PDF in the background using FastAPI `BackgroundTasks`.
- **In-Memory File Handling:** Reads PDF bytes directly into memory without saving to disk, optimizing for ephemeral cloud deployments.
- **Strict Schema Extraction:** Uses Groq's JSON mode to guarantee a predictable response structure.
- **Persistent Job State:** Uses a local SQLite database to track job status (`processing`, `complete`, `failed`).
- **Graceful Error Handling:** Automatically detects unreadable/scanned PDFs and returns a structured error state.

## Tech Stack

- **Framework:** FastAPI (Python)
- **LLM Provider:** Groq API (`llama-3.3-70b-versatile`)
- **PDF Parser:** `pypdf`
- **Database:** `sqlite3` (built-in)

---

## Local Setup

### 1. Clone the repository

```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```
