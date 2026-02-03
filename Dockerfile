FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including libmagic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a user to avoid running as root (good practice, often required)
RUN useradd -m -u 1000 user \
    && chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the port Hugging Face Spaces expects (7860)
EXPOSE 7860

# Run the application
CMD ["/bin/bash", "-c", "python build_rag.py && uvicorn api:app --host 0.0.0.0 --port 7860"]
