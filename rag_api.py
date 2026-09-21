from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import chromadb
import requests
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="RAG API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api_key = os.getenv("Gemini_API_Key")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

os.environ["GEMINI_API_KEY"] = api_key
gemini_client = genai.Client()
MODEL = "gemini-3.6-flash"

# --- ChromaDB setup ---
db_client = chromadb.PersistentClient(path="chroma_db")
client = db_client
collection = client.get_or_create_collection("documents")

# --- Schemas ---
class AskRequest(BaseModel):
    question: str
    n_results: int = 3
    max_distance: float = 1.2

class SourceChunk(BaseModel):
    text: str
    source: str
    distance: float

class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: str

# --- RAG Logic ---
SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Answer ONLY from the provided context. "
    "If the context doesn't contain the answer, say you don't have enough "
    "information. Cite source documents. Keep responses under 200 words."
)

def retrieve(question: str, n_results: int, max_distance: float):
    if collection.count() == 0:
        return []
    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, collection.count())
    )
    chunks = []
    for i in range(len(results['documents'][0])):
        dist = results['distances'][0][i]
        if dist <= max_distance:
            chunks.append(SourceChunk(
                text=results['documents'][0][i],
                source=results['metadatas'][0][i].get('source', 'unknown'),
                distance=round(dist, 4)
            ))
    return chunks

def get_confidence(chunks):
    if not chunks:
        return "none"
    best = chunks[0].distance
    if best < 0.5: return "high"
    if best < 1.0: return "medium"
    return "low"

def generate(system_prompt: str, user_message: str):
    try:
        # Format messages for Google Generative AI API
        full_prompt = f"{system_prompt}\n\n{user_message}"
        r = gemini_client.models.generate_content(
            model=MODEL,
            contents=full_prompt
        )
        return r.text
    except Exception as e:
        raise HTTPException(503, f"Gemini error: {str(e)}")

# --- Endpoints ---
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    chunks = retrieve(req.question, req.n_results, req.max_distance)
    confidence = get_confidence(chunks)

    if not chunks:
        return AskResponse(
            answer="I don't have relevant information to answer that.",
            sources=[], confidence="none"
        )

    context = "\\n\\n".join(
        f"[Source: {c.source}]\\n{c.text}" for c in chunks
    )
    system_prompt = f"{SYSTEM_PROMPT}\\n\\nCONTEXT:\\n{context}"
    answer = generate(system_prompt, req.question)
    return AskResponse(answer=answer, sources=chunks, confidence=confidence)

@app.post("/ingest")
def ingest_documents():
    docs_dir = "docs"
    if not os.path.exists(docs_dir):
        raise HTTPException(404, "docs/ directory not found")

    chunks, ids, metadatas = [], [], []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(('.txt', '.md')):
            continue
        with open(os.path.join(docs_dir, filename), 'r') as f:
            content = f.read()
        paragraphs = [p.strip() for p in content.split('\\n\\n') if p.strip()]
        for i, para in enumerate(paragraphs):
            chunks.append(para)
            ids.append(f"{filename}_{i}")
            metadatas.append({"source": filename, "chunk_index": str(i)})

    if chunks:
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)

    return {"message": f"Ingested {len(chunks)} chunks from {docs_dir}/"}

@app.get("/stats")
def stats():
    return {
        "document_count": collection.count(),
        "gemini_model": MODEL,
        "db_path": "chroma_db"
    }

@app.get("/health")
def health():
    gemini_ok = False
    try:
        r = gemini_client.models.list()
        gemini_ok = True
    except:
        pass
    return {
        "chromadb": "ok",
        "gemini": "ok" if gemini_ok else "unavailable",
        "documents": collection.count()
    }
