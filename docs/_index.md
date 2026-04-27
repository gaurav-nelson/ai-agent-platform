---
title: AI Agent Platform
date: 2026-04-27
tier: sandbox
summary: Deploy an AI agent platform on Red Hat OpenShift using the Bee AI Framework with IBM Granite models.
rh_products:
  - Red Hat OpenShift Container Platform
  - Red Hat OpenShift AI
industries:
  - General
aliases: /ai-agent-platform/
pattern_logo: ai-agent-platform.png
links:
  github: https://github.com/validatedpatterns/ai-agent-platform
  install: getting-started
  bugs: https://github.com/validatedpatterns/ai-agent-platform/issues
  feedback: https://docs.google.com/forms/d/e/1FAIpQLScI76b6tD1WyPu2-d_9CCVDr3Fu5jYERthqLKJDUGwqBg7Vcg/viewform
---

# AI Agent Platform

The AI Agent Platform pattern deploys a complete infrastructure for running AI agents on Red Hat OpenShift Container Platform. It uses the [Bee AI Framework](https://github.com/i-am-bee/beeai-framework) for agent orchestration and IBM Granite models served through vLLM for inference. The pattern provides the building blocks for enterprise AI agent deployments and includes two demo agents that you can customize or replace with your own.

## Background

AI agents extend large language models (LLMs) beyond simple text generation by enabling them to reason about tasks, call external tools, and take actions. Building a production-ready agent platform requires integrating several components: model serving infrastructure with GPU acceleration, an agent orchestration framework, tool execution capabilities, persistent memory, and observability.

This pattern assembles these components into a repeatable, GitOps-managed deployment. It uses the same proven infrastructure as the RAG-LLM-GitOps pattern for model serving and GPU management, and adds agent-specific services built on the Bee AI Framework.

## Architecture

The pattern deploys the following components into the `ai-agent` namespace:

| Component | Description |
|-----------|-------------|
| vLLM inference service | Serves IBM Granite 4.0-H-Small (32B total, 9B active MoE) through an OpenAI-compatible API |
| Bee agent service | Bee AI Framework with ReAct agents, custom Kubernetes tools, and OpenAPI tool generation |
| Agent chat UI | Gradio-based web interface for interacting with agents |
| Sample API | FastAPI inventory service that demonstrates the API Explorer agent |
| PGVector | PostgreSQL with vector extensions for agent memory |
| Prometheus and Grafana | Agent observability dashboards and metrics |

## Demo agents

The pattern ships with two demo agents:

- **Cluster Health Assistant** - A ReAct agent equipped with Kubernetes tools that can inspect pods, nodes, events, and deployments across your cluster. Ask it questions such as "Are there any pods failing in the default namespace?" or "What is the status of my GPU nodes?"

- **API Explorer** - An agent that dynamically generates tools from any OpenAPI specification. It ships connected to the sample inventory API and can create, list, and manage items through natural language. You can point it at your own OpenAPI specs to explore any REST API.

## GitOps framework

This pattern uses the [validated patterns framework](https://validatedpatterns.io/learn/) to manage deployment through ArgoCD. All configuration is declarative and stored in Git. The framework handles:

- Operator subscription management (NFD, NVIDIA GPU Operator, OpenShift AI, OpenShift Serverless, Service Mesh)
- Helm chart deployment with sync-wave ordering
- Secrets management through HashiCorp Vault
- Multi-cluster support through Open Cluster Management

## Next steps

- [Getting started](getting-started) - Deploy the pattern on your cluster
- [Cluster sizing](cluster-sizing) - Review hardware requirements
- [Ideas for customization](ideas-for-customization) - Extend the pattern for your use cases
- [Troubleshooting](troubleshooting) - Resolve common issues
