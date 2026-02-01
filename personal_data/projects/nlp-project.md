---
title: "Natural Language Processing project"
year: 2025
icon: "🦜"
weight: 5
description: Advanced NLP implementation showcasing Retrieval-Augmented Generation (RAG), topic modeling, and transformer-based question answering using Gemma and T5 models on the neural-bridge dataset. Includes interactive demos, toxicity detection, and comprehensive performance evaluation.

technologies:
    - "Python"
    - "Tensorflow"
    - "NumPy"
    - "Matplotlib"
    - "Seaborn"
    - "VSCode"
    - "Github"
    - "Kaggle"
    - "NLTK"
    - "Bert"
    - "Hugging Face"
---

## Project Overview

This project implements a comprehensive Question Answering system powered by Retrieval-Augmented Generation (RAG). It showcases the full data science pipeline from exploratory data analysis to model deployment, with a special focus on enhancing language model performance through external knowledge retrieval.

Built on the neural-bridge/rag-dataset-12000 dataset (containing 12,000 question-answer-context triples), the system demonstrates how modern NLP techniques can create more accurate, contextually grounded answers compared to traditional approaches.

## Key Components

### 📊 Data Engineering & Analysis
- **Extensive preprocessing** including tokenization, lemmatization, and semantic analysis
- **Statistical exploration** revealing insights about question types and document lengths
- **TF-IDF vectorization** with visual word highlighting for content analysis

### 🧠 Advanced NLP Techniques
- **Word embeddings** (Word2Vec) for semantic understanding of questions
- **Topic modeling** with BERTopic for context clustering and visualization
- **Toxicity detection** using weakly supervised learning and a BERT classifier

### 🔎 Retrieval & Generation
- **Dense retrieval** with Sentence Transformers (all-MiniLM-L6-v2)
- **Sparse retrieval** using TF-IDF for lexical matching
- **Answer generation** with Google's Gemma-2b language model
- **Comprehensive evaluation** using BERTScore, ROUGE metrics, and F1 score

### 🚀 Interactive Features
- **Semantic search** for finding similar questions
- **Comparative analysis** between zero-shot and context-enhanced answers
- **Audio synthesis** providing verbalized summaries via Google TTS
- **User-friendly UI** built with Gradio for demo purposes

## Results & Findings

The system demonstrated significant improvements in answer quality when using the RAG approach compared to context-free generation:

- Context-enhanced answers from Gemma achieved a BERTScore F1 of 0.91 (vs. 0.86 without context)
- Semantic search successfully identified relevant contexts for accurate answer generation
- The toxicity detection system identified potentially problematic content with high precision
- Model comparisons showed Gemma consistently outperforming T5 across all evaluation metrics

This project demonstrates how modern retrieval techniques can augment even smaller language models to produce highly accurate answers by grounding them in relevant factual contexts.

---

*This project was developed for the Natural Language Processing Course a.y. 2024/2025 at Politecnico di Milano.*

**GitHub Repository**: [https://github.com/martinimarcello00/NLP-project](https://github.com/martinimarcello00/NLP-project)