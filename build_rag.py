import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
PROJECTS_DIR = "./personal_data/projects"
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def build_rag():
    print("🚀 Starting RAG build process...")
    
    if not os.path.exists(PROJECTS_DIR):
        print(f"❌ Directory {PROJECTS_DIR} does not exist.")
        return

    # Load documents
    print(f"📂 Loading documents from {PROJECTS_DIR}...")
    loader = DirectoryLoader(PROJECTS_DIR, glob="**/*.md", loader_cls=UnstructuredFileLoader)
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} documents")

    if not documents:
        print("⚠️ No documents found. Skipping RAG build.")
        return

    # Split documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks")

    # Initialize Embeddings
    print(f"🧠 Initializing embeddings model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # Store in ChromaDB
    print(f"💾 Creating/Updating ChromaDB at {CHROMA_DB_DIR}...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"🎉 Data successfully stored in ChromaDB at {CHROMA_DB_DIR}!")

if __name__ == "__main__":
    build_rag()
