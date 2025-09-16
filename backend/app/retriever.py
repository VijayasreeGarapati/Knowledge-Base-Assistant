import os
# LangChain core
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# LangChain community extensions
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# HuggingFace
from transformers import pipeline


def load_embeddings():
    """Use OpenAI if key present, else Hugging Face embeddings"""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"))
    else:
        model_name = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        return HuggingFaceEmbeddings(model_name=model_name)


def load_llm():
    """Use OpenAI if key present, else Hugging Face LLM"""
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
        )
    else:
        model_name = os.getenv("HF_MODEL", "google/flan-t5-base")
        hf_pipeline = pipeline("text2text-generation", model=model_name)
        return HuggingFacePipeline(pipeline=hf_pipeline)


def get_vectorstore(top_k=4):
    """Load FAISS vector store"""
    if not os.path.exists("data/faiss_index"):
        raise ValueError("No FAISS index found. Run ingest.py first.")
    return FAISS.load_local("data/faiss_index", load_embeddings(), allow_dangerous_deserialization=True)


def get_rag_chain(top_k=4):
    embeddings = load_embeddings()
    vectorstore = get_vectorstore(top_k=top_k)

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    llm = load_llm()

    prompt_template = """
    You are a helpful assistant. Use the following context to answer the question.
    If you don't know, say "I don’t know". Always cite your sources.

    Context:
    {context}

    Question: {question}
    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
        input_key="question"
    )

    def invoke(inputs):
        result = qa_chain.invoke(inputs)
        answer = result["result"]
        sources = [{"source": d.metadata.get("source", ""), "content": d.page_content[:300]} for d in result["source_documents"]]
        return {"answer": answer, "sources": sources}

    return type("RAGWrapper", (), {"invoke": staticmethod(invoke)})