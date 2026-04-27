# AI Agent Platform with Bee AI Framework

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This is a validated pattern that deploys an **AI Agent Platform** on Red Hat OpenShift using the [Bee AI Framework](https://github.com/i-am-bee/beeai-framework) with IBM Granite models.

## Overview

This pattern provides a **building block** for enterprise AI agent deployments. It ships the complete infrastructure for running AI agents — LLM serving, agent orchestration, tool execution, memory, and observability — and includes two demo agents that users can customize or replace.

### Demo Agents

- **Cluster Health Assistant** — A ReAct agent with Kubernetes tools that can inspect pods, nodes, events, and deployments across your cluster
- **API Explorer** — An agent that dynamically generates tools from any OpenAPI specification, shipped with a sample inventory REST API

### Architecture

| Component | Description | Image |
|---|---|---|
| vLLM Inference Service | Serves IBM Granite 4.0-H-Small (32B/9B active MoE) via OpenAI-compatible API | `quay.io/modh/vllm:rhoai-2.20-cuda` |
| Bee Agent Service | Bee AI Framework with ReAct agents and custom tools | `quay.io/validatedpatterns/bee-agent-service` |
| Agent Chat UI | Gradio-based web interface for interacting with agents | `quay.io/validatedpatterns/agent-chat-ui` |
| Sample API | FastAPI inventory service for the API Explorer demo | `quay.io/validatedpatterns/sample-api` |
| PGVector | PostgreSQL with vector extensions for agent memory | `docker.io/pgvector/pgvector:pg17` |
| Prometheus + Grafana | Agent observability and metrics dashboards | Community operators |

### Prerequisites

- OpenShift 4.12+
- Cluster-admin access
- GPU node (provisioned via `make create-gpu-machineset`)
- HuggingFace token for model download

## Getting Started

1. Fork this repository
2. Clone your fork and `cd` into it
3. Copy `values-secret.yaml.template` to `values-secret.yaml` and fill in your HuggingFace token
4. Run `make install` or use the Validated Patterns Operator
5. After initial deployment, run `make create-gpu-machineset` to provision a GPU node

## Customization

This pattern is designed as a building block. To customize:

- **Add your own agents**: Create new agent modules in `containers/bee-agent-service/app/agents/`
- **Add your own tools**: Create new tool classes in `containers/bee-agent-service/app/tools/`
- **Connect your own APIs**: Point the API Explorer at your OpenAPI specs
- **Load your own documents**: Use PGVector for RAG-based agent memory

## Documentation

Full documentation is available at [validatedpatterns.io](https://validatedpatterns.io/patterns/ai-agent-platform/).
