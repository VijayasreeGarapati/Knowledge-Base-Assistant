import argparse
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .retriever import load_embeddings
from langchain_community.vectorstores import FAISS


def ingest_docs(docs_dir: str):
    docs = []

    # Load all .txt files
    txt_loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    docs.extend(txt_loader.load())

    # Load all .pdf files
    pdf_loader = DirectoryLoader(
        docs_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    docs.extend(pdf_loader.load())

    if not docs:
        print("No documents found in the given directory.")
        return

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    # Build vectorstore
    embeddings = load_embeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    os.makedirs("data", exist_ok=True)
    vectorstore.save_local("data/faiss_index")
    print(f"Ingested {len(split_docs)} chunks from {len(docs)} files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs_dir", required=True)
    args = parser.parse_args()
    ingest_docs(args.docs_dir)