FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Bake the ONNX embedding model and the vector index into the image. The Space has an
# ephemeral disk and restarts often, so anything built at boot is paid for every time.
ENV FASTEMBED_CACHE_DIR=/app/.fastembed_cache
RUN python -c "from embeddings import get_embeddings; get_embeddings().embed_query('warmup')" \
    && python build_index.py

# Create a user to avoid running as root (good practice, often required)
RUN useradd -m -u 1000 user \
    && chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port Hugging Face Spaces expects (7860)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
