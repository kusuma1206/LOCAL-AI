import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_retrieval_flow, run_ingestion_pipeline
from processing.storage import supabase

print("--- API Server Initializing ---")

app = FastAPI()

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "online", "message": "SLM RAG API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class QueryRequest(BaseModel):
    query: str
    mode: str

class QueryHistoryRequest(BaseModel):
    query: str
    mode: str
    history: list[dict] = []

@app.post("/query")
def query_system(request: QueryRequest):
    # Backward compatibility
    from retrieval import mode_router
    result = mode_router.handle_query(supabase, request.query, request.mode)
    return {"result": result}

@app.post("/chat")
def chat_system(request: QueryHistoryRequest):
    """
    Handles conversational RAG with history.
    """
    from retrieval import mode_router
    result = mode_router.handle_query(supabase, request.query, request.mode, request.history)
    return {"result": result}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Handles document upload, saves to uploads folder, and triggers the ingestion pipeline.
    """
    suffix = os.path.splitext(file.filename)[1]
    if suffix.lower() not in ['.pdf', '.docx', '.md']:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Trigger ingestion
        run_ingestion_pipeline(file_path)
        
        return {
            "status": "success",
            "message": "Upload successful",
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """
    Retrieves unique document IDs from the sections table.
    """
    try:
        # Simple retrieval from sections table
        response = supabase.table("sections").select("document_id").execute()
        
        # Get unique IDs
        doc_ids = list(set([item['document_id'] for item in response.data]))
        
        # Map to a more friendly format
        documents = [{"id": doc_id, "name": f"Document {doc_id[:8]}..."} for doc_id in doc_ids]
        
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
