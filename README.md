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

An autonomous agent that answers questions about Marcello Martini's professional profile and portfolio.

## Features

- **RAG/Tools**: Accesses structured YAML data (Experience, Education) and Markdown projects.
- **Agentic**: Uses LangGraph to plan and execute tool calls.
- **Rate Limited**: Protects against abuse.
- **Persistent**: Remembers context within a session (windowed memory).
- **Projects**: Can search and retrieve details about portfolio projects.

## Setup locally

1. Clone repo
2. `pip install -r requirements.txt`
3. Set `.env` with `OPENAI_API_KEY`
4. `uvicorn api:app --reload`

## Deployment

This repository is synced to Hugging Face Spaces via GitHub Actions.
It uses a Docker container to serve the FastAPI backend.
