import os
import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# CHANGE: Import HuggingFace Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("RAG")

# Configuration
PDF_FOLDER = "knowledge_base"
DB_PATH = "chroma_db"

# CHANGE: Initialize Local Embeddings (Runs on CPU, No API Limits)
# This downloads a small model (~80MB) once.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def build_vector_store():
    """
    Loads PDFs, splits them, and builds/updates the vector database.
    """
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        logger.warning(f"⚠️ Created folder '{PDF_FOLDER}'. Please put PDF files there.")
        return None

    logger.info("📚 Loading PDFs...")
    loader = PyPDFDirectoryLoader(PDF_FOLDER)
    docs = loader.load()

    if not docs:
        logger.warning("⚠️ No PDFs found in knowledge_base folder.")
        return None

    logger.info(f"📄 Loaded {len(docs)} pages. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)

    logger.info(f"💾 Found {len(chunks)} chunks. Saving to ChromaDB (Local Mode)...")

    # No batching needed for local models, but good practice to keep it simple
    try:
        # If DB exists, delete it to avoid conflicts with old embeddings
        if os.path.exists(DB_PATH):
            import shutil
            shutil.rmtree(DB_PATH)
            logger.info("🗑️ Cleared old database to ensure compatibility.")

        vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=embeddings, 
            persist_directory=DB_PATH
        )
        vector_store.persist()
        logger.info("✅ Knowledge Base Built Successfully!")
        return vector_store

    except Exception as e:
        logger.error(f"❌ Error building database: {e}")
        return None

def get_rag_context(query: str):
    """
    Searches the vector DB for relevant context.
    """
    if not os.path.exists(DB_PATH):
        logger.info("⚠️ DB not found, building now...")
        build_vector_store()

    try:
        vector_store = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
        # Search for top 3 relevant chunks
        results = vector_store.similarity_search(query, k=3)
        
        if not results:
            return ""
            
        context_text = "\n\n".join([doc.page_content for doc in results])
        return context_text
    except Exception as e:
        logger.error(f"RAG Search Error: {e}")
        return ""

# Helper to run build manually
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_vector_store()