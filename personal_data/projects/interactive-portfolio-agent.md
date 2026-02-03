---
title: "Interactive Portfolio Agent"
year: 2025
icon: "🤖"
weight: 3
description: Autonomous agent designed to answer questions about my professional profile, portfolio, and expertise using RAG and LangGraph.
technologies:
    - "Python"
    - "LangGraph"
    - "RAG"
    - "Docker"
    - "FastAPI"
    - "Gradio"
    - "OpenAI"
    - "ChromaDB"
    - "Hugging Face Spaces"
---

**[Go to the GitHub Repository](https://github.com/martinimarcello00/langgraph-cv-agent)**

**[Try it out on Hugging Face Spaces](https://martinimarcello00-langgraph-cv-agent.hf.space/) or click the button in the bottom right corner of the screen.**

## 🚀 Project Overview

The **Interactive Portfolio Agent** is an autonomous system capable of answering detailed questions about my professional background, projects, and skills. It acts as an interactive version of my CV, leveraging **LangGraph** for orchestration and **Retrieval Augmented Generation (RAG)** to provide accurate, context-aware responses based on my actual portfolio data.

## ✨ Key Features

- **Autonomous Reasoning**: Uses **LangGraph** to plan multi-step actions and execute tool calls efficiently.
- **RAG & Tool Integration**:
  - **Portfolio Retrieval**: Searches and retrieves details about specific projects from markdown files.
  - **Structured Data Access**: Queries structured YAML data for Experience, Education, and Certifications.
- **Persistent Memory**: Maintains conversation context to support follow-up questions.
- **Robustness & Security**: Includes rate limiting and token usage tracking.
- **Interactive UI**: Features a user-friendly **Gradio** interface and exposing a **FastAPI** endpoint.

## 🛠️ Architecture

The agent is built with a focus on modularity and deployment:

- **LangGraph**: Manages the agent's state and decision-making process.
- **ChromaDB**: Stores the vector embeddings for the RAG system.
- **FastAPI**: Serves the agent as a REST API.
- **Docker**: Ensures consistent deployment across environments, including Hugging Face Spaces.
