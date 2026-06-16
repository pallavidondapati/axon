import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── globals ───────────────────────────────────────
vectorstore = None
retriever = None
faiss_lock = Lock()  # Synchronization: lock on FAISS writes
FAISS_PATH = "./faiss_index"

# ── embeddings ────────────────────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./models"
)

# ── PDF loading (Multi-threading) ─────────────────
def load_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    # multi-threaded chunking across pages
    with ThreadPoolExecutor(max_workers=4) as executor:
        chunks_nested = list(executor.map(
            lambda doc: splitter.split_documents([doc]),
            documents
        ))
    # flatten
    return [chunk for sublist in chunks_nested for chunk in sublist]

# ── vectorstore (Scalable System Design) ──────────
def create_vectorstore(chunks):
    global vectorstore, retriever
    with faiss_lock:  # synchronized FAISS write
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(FAISS_PATH)  # persist to disk
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return vectorstore

def load_existing_vectorstore():
    """Load persisted FAISS index on startup if it exists."""
    global vectorstore, retriever
    if os.path.exists(FAISS_PATH):
        with faiss_lock:
            vectorstore = FAISS.load_local(
                FAISS_PATH, embeddings,
                allow_dangerous_deserialization=True
            )
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ── RAG query ─────────────────────────────────────
def query_rag(question: str, llm) -> str:
    if retriever is None:
        return "No document loaded. Please upload a PDF first."

    prompt = ChatPromptTemplate.from_template("""
    Answer the question based on the context below.
    If you don't know the answer from the context, say so and if user asks another query which is not related to document answer it with your own knowledge only if it present in the document use the document or pdf data and answer based on it and lastly give that this answer was based on the document or pdf you have sent me
    Context: {context}
    Question: {question}
    Answer:""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)

# ── file upload handler ───────────────────────────
def process_uploaded_file(uploaded_file) -> str:
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    chunks = load_pdf(file_path)
    create_vectorstore(chunks)
    return f"✅ {uploaded_file.name} loaded — {len(chunks)} chunks created"

def is_rag_ready() -> bool:
    return retriever is not None

# load existing index on import
load_existing_vectorstore()