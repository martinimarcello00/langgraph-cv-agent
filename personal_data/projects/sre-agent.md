---
title: "SRE Agent: Autonomous Kubernetes Operations"
year: 2024 - 2025
icon: "🤖"
weight: 1
description: Autonomous agent for Kubernetes incident detection, diagnosis, and mitigation using LLMs and modular workflows.
technologies:
    - "Python"
    - "LangChain"
    - "LangGraph"
    - "Kubernetes"
    - "Prometheus"
    - "Jupyter notebook"
    - "Poetry"
    - "Docker"
    - "Model Context Protocol"
---

**[Go to the GitHub Repository](https://github.com/martinimarcello00/SRE-agent)**


## 🚀 Project Overview

The **SRE Agent** is an autonomous multi-agent system designed to automate Incident Response in Kubernetes environments. By leveraging Large Language Models (LLMs) and a **Divide & Conquer** strategy, it significantly reduces the Mean Time to Resolution (MTTR) for complex microservice faults.

This system integrates with **AIOpsLab** for realistic fault injection and uses a custom **Model Context Protocol (MCP)** server to interface with observability tools (Prometheus, Jaeger, Kubernetes API) securely and efficiently.

## 🤖 Architecture & Key Features

![SRE Agent Architecture](/images/sre_agent_architecture.png)

The agent implements a parallel multi-agent workflow to diagnose faults efficiently.

### Core Components

- **🔍 Triage Agent (Hybrid)**: Detects symptoms explicitly. It combines deterministic heuristics (based on the Four Golden Signals: Latency, Errors, Saturation) with LLM reasoning. This hybrid approach grounds the diagnosis in hard evidence to minimize hallucinations.
- **📋 Planner Agent (Topology-Aware)**: Strategies the investigation. Uses a **Graph-Based Datagraph** to understand cluster topology (dependencies, upstream services). It generates a deduplicated, prioritized list of RCA Tasks, assigning specific investigation goals and target resources.
- **🔬 RCA Workers (Parallel Execution)**: Execute the investigation using a **Divide & Conquer** approach. Multiple workers run in parallel, each handling a specific task. They use MCP tools (Logs, Traces, Metrics) to gather evidence and produce a diagnostic report. A deterministic RCA Router manages task dispatching.
- **👔 Supervisor Agent**: The Final Decision Maker. Aggregates worker reports to synthesize a final Root Cause Analysis. It can either finalize the diagnosis or trigger a feedback loop to schedule pending tasks if more evidence is needed.

### Key Features

- **Datagraph**: A graph representation of the cluster topology (Infrastructure & Data dependencies) that guides the agent, preventing irrelevant resource exploration.
- **Custom MCP Server**: Standardizes tool interaction and performs "pre-digestion" of data (e.g., retrieving only relevant metrics or error logs) to optimize context window usage and reduce token costs.

## 🧪 Automated Evaluation Pipeline

The repository includes a robust pipeline for automated experimentation and benchmarking.

### Framework
- **Integration**: Built on top of **AIOpsLab** to deploy testbeds (Hotel Reservation, Social Network) and inject realistic faults (Network delays, Pod failures, Misconfigurations).
- **Batch Execution**: `automated_experiment.py` orchestrates end-to-end batch runs: Cluster Setup → Fault Injection → Agent Execution → Evaluation → Cleanup.

### Metrics
The system is evaluated on:
1. **Detection Accuracy**: Correct identification of an anomaly.
2. **Localization Accuracy**: Correct identification of the root cause resource (Service/Pod).
3. **RCA Score**: Semantic evaluation of the diagnosis using LLM-as-a-Judge (1-5 scale with rationale).

## 📁 Repository Structure

```text
SRE-agent/
├── sre-agent/        # 🧠 Main Multi-Agent System implementation (LangGraph)
├── MCP-server/       # 🔌 Custom Model Context Protocol server for observability tools
├── notebooks/        # 📓 Jupyter notebooks for analysis and development
├── Results/          # 📊 Experiment outputs, logs, and reports
├── archive/          # 📦 Archive of previous project iterations
└── assets/           # 🖼️ Diagrams and static assets
```

## 🔗 Links & Resources

- **[GitHub Repository](https://github.com/martinimarcello00/SRE-agent)**: Complete source code and implementation.
