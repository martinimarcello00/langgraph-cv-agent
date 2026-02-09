import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
PROJECTS_DIR = "./personal_data/projects"
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

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

    # Split by Markdown headers first (semantic chunking)
    print("🔪 Performing semantic chunking by headers...")
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    # Process each document
    header_splits = []
    for doc in documents:
        try:
            splits = markdown_splitter.split_text(doc.page_content)
            for split in splits:
                split.metadata.update(doc.metadata)
            header_splits.extend(splits)
        except Exception as e:
            print(f"⚠️ Warning: Could not split {doc.metadata.get('source', 'unknown')}: {e}")
            header_splits.append(doc)
    
    print(f"✅ Split into {len(header_splits)} sections by headers")

    # Then apply character-based chunking with optimized parameters
    print("✂️ Applying recursive text splitting...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,  # Reduced from 1000 for better precision
        chunk_overlap=100,  # Reduced from 200
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    
    chunks = text_splitter.split_documents(header_splits)
    print(f"✂️ Final chunks: {len(chunks)}")

    # Initialize Embeddings with optimization
    print(f"🧠 Initializing embeddings model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={
            'normalize_embeddings': True,
            'batch_size': 32
        }
    )

    # Enrich metadata
    print("🏷️ Enriching metadata...")
    for chunk in chunks:
        source = chunk.metadata.get('source', '')
        if 'projects' in source:
            chunk.metadata['doc_type'] = 'project'
        # Extract year if available
        if 'year' in chunk.metadata:
            try:
                chunk.metadata['year'] = int(chunk.metadata['year'])
            except:
                pass

    # Store in ChromaDB
    print(f"💾 Creating/Updating ChromaDB at {CHROMA_DB_DIR}...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"🎉 Data successfully stored in ChromaDB at {CHROMA_DB_DIR}!")
    print(f"📊 Total chunks indexed: {len(chunks)}")

if __name__ == "__main__":
    build_rag()
