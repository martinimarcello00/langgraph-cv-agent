"""Single source for the embedding function.

The index and the query side must use the same model or retrieval silently returns
noise, so both `build_rag.py` and `tools.py` import from here.
"""

import os
from functools import lru_cache

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# fastembed defaults to the system temp dir, which would re-download on every
# container start. Pinning it lets the Dockerfile bake the model into a layer.
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", os.path.join(BASE_DIR, ".fastembed_cache"))


@lru_cache(maxsize=1)
def get_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL_NAME, cache_dir=CACHE_DIR)
