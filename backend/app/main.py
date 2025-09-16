from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel
from .retriever import get_rag_chain
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware # type: ignore


# Load env from root
load_dotenv()

app = FastAPI(title="KB-Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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