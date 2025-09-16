from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .retriever import get_rag_chain
from dotenv import load_dotenv
import os

# Load env from root
load_dotenv()

app = FastAPI(title="KB-Assistant")

class QueryRequest(BaseModel):
    query: str
    top_k: int = 4

# Initialize RAG pipeline
rag_chain = get_rag_chain(top_k=int(os.getenv("TOP_K", 4)))

@app.post("/query")
async def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    result = rag_chain.invoke({"question": req.query})
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }