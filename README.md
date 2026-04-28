# Async Document Processor

An asynchronous FastAPI service that accepts PDF uploads, extracts text in the background, and uses Groq's `llama-3.3-70b-versatile` model to classify the document and return structured JSON.

The API is designed for simple document workflows such as invoices, forms, and other text-based PDFs. It stores job state in SQLite, so you can submit a file, get back a `job_id`, and poll for the final result later.

## What It Does

- Accepts a PDF upload at `/process-document`.
- Processes the file in the background and returns immediately with a `job_id`.
- Extracts text directly from memory without writing the upload to disk.
- Stores job status and the final payload in a local SQLite database.
- Returns a predictable JSON response, or a structured failure if extraction or model processing fails.

## Tech Stack

- FastAPI
- Groq API
- `pypdf`
- SQLite (`sqlite3` from the Python standard library)
- `python-dotenv`

## Requirements

- Python 3.10 or newer
- A Groq API key

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv venv
venv\\Scripts\\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Run

Start the server with Uvicorn:

```bash
uvicorn main:app --reload
```

Then open `http://127.0.0.1:8000/docs` to try the endpoints from the built-in Swagger UI.

## API

### `POST /process-document`

Upload a PDF file as `multipart/form-data` with the field name `file`.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/process-document" \
	-F "file=@invoice.pdf"
```

Response:

```json
{
  "job_id": "b6db7f2a-5d8c-4f5c-9d9e-1d5c8f6f2d7b",
  "status": "processing"
}
```

### `GET /result/{job_id}`

Poll for the final result using the `job_id` returned by the upload endpoint.

Example:

```bash
curl "http://127.0.0.1:8000/result/b6db7f2a-5d8c-4f5c-9d9e-1d5c8f6f2d7b"
```

Possible responses:

- `processing` while the background task is still running.
- `complete` with the extracted JSON payload.
- `failed` with an error message if the PDF could not be read or the model call failed.

## Output Shape

Successful jobs return data shaped like this:

```json
{
  "job_id": "...",
  "status": "complete",
  "document_type": "invoice",
  "confidence": 0.96,
  "extracted_fields": {
    "document_date": "2026-04-28",
    "total_amount": 1250.0,
    "counterparty": "Acme Corp"
  },
  "page_count": 2,
  "processing_time_ms": 842,
  "error": null
}
```

If the PDF is scanned or unreadable, the job is marked as `failed` with an error string.

## How It Works

1. The upload endpoint creates a new job in `jobs.db` with status `processing`.
2. The PDF bytes are read into memory and passed to a background task.
3. `pypdf` extracts the text from each page.
4. Groq returns JSON describing the document type and selected fields.
5. The final payload is written back to SQLite and can be fetched later by job ID.

## Project Files

- [main.py](main.py) - FastAPI app, background processing, and SQLite job storage.
- [requirements.txt](requirements.txt) - Python dependencies.
- [README.md](README.md) - Project overview and usage.

## Notes

- The app creates `jobs.db` automatically in the project root.
- The Groq client is only initialized when `GROQ_API_KEY` is present.
- This implementation is best suited for text-based PDFs; scanned PDFs will usually fail text extraction.

## Troubleshooting

- If `/process-document` returns `500`, verify that `GROQ_API_KEY` is set.
- If a job stays in `processing`, refresh the result endpoint after the background task completes.
- If extraction fails on a PDF, try a text-based file rather than a scanned image-only document.
