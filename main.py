import sqlite3
import uuid
import time
import json
import io
import os
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pypdf import PdfReader
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from the .env file safely
load_dotenv()

app = FastAPI()

# Safely get the key from the environment
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def init_db():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT,
            result_json TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def process_pdf_background(job_id: str, file_content: bytes):
    try:
        reader = PdfReader(io.BytesIO(file_content))
        page_count = len(reader.pages)
        text = "".join([page.extract_text() or "" for page in reader.pages])
            
        if not text.strip():
            raise ValueError("Could not extract text — PDF appears to be scanned")

        start_time = time.time()
        prompt = f"""
        Analyze this text and extract the fields as JSON. 
        Return ONLY valid JSON matching this structure exactly, with null for missing fields:
        {{"document_type": "string", "confidence": float, "extracted_fields": {{"document_date": "string/null", "total_amount": float/null, "counterparty": "string/null"}}}}
        
        Text: {text[:4000]}
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        llm_result = json.loads(response.choices[0].message.content)
        
        final_result = {
            "job_id": job_id,
            "status": "complete",
            "document_type": llm_result.get("document_type"),
            "confidence": llm_result.get("confidence"),
            "extracted_fields": llm_result.get("extracted_fields", {
                "document_date": None, "total_amount": None, "counterparty": None
            }),
            "page_count": page_count,
            "processing_time_ms": processing_time_ms,
            "error": None
        }

    except Exception as e:
        final_result = {
            "job_id": job_id,
            "status": "failed",
            "document_type": None,
            "confidence": None,
            "extracted_fields": {"document_date": None, "total_amount": None, "counterparty": None},
            "page_count": locals().get('page_count'),
            "processing_time_ms": None,
            "error": str(e)
        }

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ?, result_json = ? WHERE job_id = ?", 
                  (final_result["status"], json.dumps(final_result), job_id))
    conn.commit()
    conn.close()

@app.post("/process-document")
async def process_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not client:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
        
    job_id = str(uuid.uuid4())
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO jobs (job_id, status) VALUES (?, ?)", (job_id, "processing"))
    conn.commit()
    conn.close()
    
    file_content = await file.read()
    background_tasks.add_task(process_pdf_background, job_id, file_content)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, result_json FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    status, result_json = row
    if status == "processing":
        return {"job_id": job_id, "status": "processing"}
        
    return json.loads(result_json)