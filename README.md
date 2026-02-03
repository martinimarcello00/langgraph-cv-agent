---
title: LangGraph CV Agent
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
license: mit
short_description: Autonomous agent for Marcello Martini's profile & portfolio.
tags:
  - agent
  - langgraph
  - cv
  - portfolio
---

# LangGraph CV Agent

An autonomous agent designed to answer questions about Marcello Martini's professional profile, portfolio, and expertise. This agent leverages **LangGraph** for orchestration and **RAG (Retrieval Augmented Generation)** to provide accurate, context-aware responses based on structured data and project documentation.

## ✨ Features

- **Autonomous Reasoning**: Uses **LangGraph** to plan multi-step actions and execute tool calls efficiently.
- **RAG & Tool Integration**:
  - **Portfolio Retrieval**: Searches and retrieves details about specific projects from markdown files.
  - **Structured Data Access**: Queries structured YAML data for Experience, Education, and Certifications.
  - **Email Capability**: Can send emails via Mailgun (optional).
- **Persistent Memory**: Maintains conversation context with a windowed memory (last 6 messages) to support follow-up questions.
- **Robustness & Security**:
  - **Rate Limiting**: Integrated `slowapi` to limit requests (e.g., 5 requests/minute) protecting the API.
  - **Token Usage Tracking**: Monitors execution to stay within a daily defined token budget.
- **Interactive UI**: Built-in **Gradio** interface for easy interaction.
- **API First**: Exposes a FastAPI endpoint for programmatic access.

## 🚀 Setup locally

### Prerequisites
- Python 3.10+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/martinimarcello00/langgraph-cv-agent.git
   cd langgraph-cv-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   Copy the example environment file and configure your keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `OPENAI_API_KEY`.

5. **Build RAG Index & Run**
   The application builds the RAG index on startup, but you can run it manually:
   ```bash
   python build_rag.py
   uvicorn api:app --reload --port 8000
   ```
   Access the UI at `http://localhost:8000`.

## 🔑 Environment Variables

See `.env.example` for a complete list.

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API Key (GPT-4o/GPT-5-nano). | **Yes** |
| `OPENAI_ADMIN_API_KEY`| Fallback key for usage tracking if distinct from main key. | No |
| `DAILY_TOKEN_LIMIT` | Max tokens per day (default `50000`). | No |
| `MAILGUN_API_KEY` | API Key for Mailgun (if email features needed). | No |
| `MAILGUN_URL` | Mailgun API Base URL. | No |
| `MAILGUN_SENDER` | Sender email address for Mailgun. | No |

## 🛠️ API Endpoint

The agent exposes a REST API via FastAPI.

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "message": "What is Marcello's latest project?",
  "thread_id": "user-session-123"
}
```

**Response:**
```json
{
  "response": "Marcello's latest project is..."
}
```

## ☁️ Hosting on Hugging Face Spaces

This project is configured to deploy easily to **Hugging Face Spaces** using the Docker SDK.

### 1. Create a Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and create a new Space.
2. Select **Docker** as the SDK.

### 2. Configure Secrets (on Hugging Face)
In your Space settings, go to the **Settings** tab and find **Variables and secrets**.
Add the following **Secrets**:
- `OPENAI_API_KEY`: Your OpenAI API Key.
- (Optional) `MAILGUN_API_KEY`, etc.

### 3. Continuous Deployment (GitHub Actions)
This repo includes a GitHub Action (`.github/workflows/sync-hf-space.yml`) to automatically sync changes to your Space.

**Setup GitHub Secrets:**
1. Go to your GitHub repository **Settings** -> **Secrets and variables** -> **Actions**.
2. Add the following **Repository Secrets**:
   - `HF_TOKEN`: A Hugging Face Access Token with `write` permissions (create one in your HF settings).

3. Add the following **Repository Variables**:
   - `HF_USERNAME`: Your Hugging Face username.
   - `HF_SPACE_NAME`: The name of the Space you created (e.g., `langgraph-cv-agent`).

Once configured, every push to the `main` branch will automatically build and deploy the latest version to your Hugging Face Space.
