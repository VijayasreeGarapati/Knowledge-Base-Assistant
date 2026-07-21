from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel
from .retriever import format_source, get_rag_chain, get_rag_components, load_llm
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import StreamingResponse
import json


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
top_k = int(os.getenv("TOP_K", 4))
rag_chain = get_rag_chain(top_k=top_k)
stream_retriever, _, stream_prompt = get_rag_components(top_k=top_k)
stream_llm = load_llm(streaming=True)


def sse_event(event: str, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def chunk_text(chunk):
    if isinstance(chunk, str):
        return chunk
    if hasattr(chunk, "content"):
        return chunk.content or ""
    if isinstance(chunk, dict):
        return chunk.get("content", "")
    return str(chunk)


def stream_answer(prompt: str):
    if os.getenv("OPENAI_API_KEY") and hasattr(stream_llm, "stream"):
        for chunk in stream_llm.stream(prompt):
            text = chunk_text(chunk)
            if text:
                yield text
        return

    response = stream_llm.invoke(prompt)
    text = chunk_text(response)
    for word in text.split(" "):
        if word:
            yield f"{word} "

@app.post("/query")
async def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    result = rag_chain.invoke({"question": req.query})
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }


@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    def event_generator():
        documents = stream_retriever.get_relevant_documents(req.query)
        context = "\n\n".join(document.page_content for document in documents)
        prompt = stream_prompt.format(context=context, question=req.query)

        yield sse_event("sources", [format_source(document) for document in documents])
        for text in stream_answer(prompt):
            yield sse_event("chunk", {"text": text})
        yield sse_event("done", {})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
