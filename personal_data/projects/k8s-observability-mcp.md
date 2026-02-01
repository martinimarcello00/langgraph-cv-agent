---
title: "K8s Observability MCP server"
year: 2025
icon: "🕸️"
weight: 2
description: A comprehensive Kubernetes observability toolkit built on the Model Context Protocol (MCP) for Site Reliability Engineering.
technologies:
    - "Model Context Protocol"
    - "Kubernetes"
    - "Prometheus"
    - "Jaeger"
    - "Neo4j"
    - "Python"
    - "Poetry"
---

**[Go to the GitHub Repository](https://github.com/martinimarcello00/k8s-observability-mcp)**

## 🚀 Project Overview

The **K8s Observability MCP** is a comprehensive toolkit designed to simplify Kubernetes observability and troubleshooting. This MCP server enables seamless exploration of Kubernetes metrics, logs, traces, and service graph data through a unified interface, making it an essential tool for Site Reliability Engineers (SREs) and DevOps teams.

By leveraging the Model Context Protocol, this project bridges the gap between observability systems (Prometheus, Jaeger, Neo4j) and intelligent agents, enabling automated incident diagnosis and root cause analysis in Kubernetes environments.

## 🏗️ Architecture & Key Features

### Core Capabilities

- **📊 Metrics & Observability**: Retrieve instant and historical metrics from Prometheus for pods and services (CPU, memory, network, thread counts, container specs)
- **📜 Log Management**: Access pod/service logs with intelligent filtering for ERROR, WARN, and CRITICAL keywords
- **🔗 Service Dependencies**: Query service call chains and infrastructure dependencies (databases, caches, message queues)
- **🧵 Distributed Tracing**: Explore traces from Jaeger with detailed span information, timestamps, and error tracking
- **🧭 Cluster Overview**: Comprehensive view of all pods and services with status information

### MCP Tools

#### 🔍 Kubernetes Resource Inspection
- `get_pods_from_service(service)` - Lists all pods belonging to a specific service
- `get_cluster_pods_and_services()` - Complete cluster overview with counts

#### 📊 Metrics & Observability
- `get_metrics(resource_name, resource_type)` - Instant Prometheus metrics
- `get_metrics_range(resource_name, resource_type, time_range_minutes)` - Historical metrics over time
- `get_logs(resource_name, resource_type, tail, important)` - Retrieve and filter logs

#### 🔗 Service Dependencies & Graph
- `get_services_used_by(service)` - Downstream service dependencies
- `get_dependencies(service)` - Infrastructure dependencies and integrations

#### 🧵 Distributed Tracing
- `get_traces(service_name, only_errors)` - Service traces from Jaeger
- `get_trace(trace_id)` - Detailed trace information with spans and timing

## 🛠️ Technical Stack

- **Python 3.13+** - Primary implementation language
- **Poetry** - Dependency management and packaging
- **Kubernetes API** - Direct cluster access via kubeconfig
- **Prometheus** - Time-series metrics collection
- **Jaeger** - Distributed tracing backend
- **Neo4j** - Service graph database for dependency mapping
- **Model Context Protocol** - Standardized tool interface

## 🔧 Configuration

The project uses environment variables for flexible deployment:

```
TARGET_NAMESPACE     - Kubernetes namespace to scope queries
PROMETHEUS_URL       - Prometheus server endpoint
JAEGER_URL          - Jaeger UI endpoint for trace retrieval
NEO4J_URI           - Neo4j database connection
NEO4J_USER          - Neo4j authentication
NEO4J_PASSWORD      - Neo4j authentication
```

## 📈 Use Cases

- **Incident Response**: Quickly gather metrics, logs, and traces for root cause analysis
- **Performance Optimization**: Historical metric analysis to identify bottlenecks
- **Dependency Analysis**: Understand service topology and communication patterns
- **SRE Automation**: Enable AI agents to autonomously diagnose cluster issues
- **Troubleshooting**: Integrated view of multiple observability sources in one interface

## 🌟 Key Features

- **Kubeconfig Integration**: Uses your default Kubernetes configuration automatically
- **Neo4j Service Graph**: Builds comprehensive service dependency maps from Jaeger traces and static definitions
- **Intelligent Log Filtering**: Automatically identifies critical log entries
- **Multi-Source Integration**: Unifies data from multiple observability platforms
- **MCP Compatible**: Works with any MCP client including Claude, LangGraph agents, and custom applications

## 🚀 Getting Started

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your observability endpoints

# Run the MCP server
poetry run python mcp_server.py
```

Then connect with your MCP client to access all available tools for Kubernetes observability.
