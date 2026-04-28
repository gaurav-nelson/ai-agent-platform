---
title: Cluster sizing
weight: 20
aliases: /ai-agent-platform/cluster-sizing/
---

# Cluster sizing for AI Agent Platform

## Minimum cluster requirements

The following table lists the minimum resources required to run the AI Agent Platform pattern.

| Node role | Count | Instance type (AWS) | CPU | Memory | Storage |
|-----------|-------|---------------------|-----|--------|---------|
| Control plane | 1 | m5.2xlarge | 8 vCPU | 32 GB | 100 GB |
| Worker | 3 | m5.2xlarge | 8 vCPU | 32 GB | 200 GB |
| GPU | 1 | g6.2xlarge | 8 vCPU | 32 GB | 200 GB |

> **Note:** The GPU node is provisioned separately after the initial cluster deployment by using `make create-gpu-machineset`. It is not part of the initial cluster configuration.

## Component resource requirements

The following table breaks down CPU and memory requests and limits for each component deployed in the `ai-agent` namespace.

| Component | CPU request | CPU limit | Memory request | Memory limit |
|-----------|-------------|-----------|----------------|--------------|
| vLLM inference service | 4 CPU | 8 CPU | 8 Gi | 16 Gi |
| Bee agent service | 500m | 2 CPU | 512 Mi | 2 Gi |
| Agent chat UI | 250m | 1 CPU | 256 Mi | 1 Gi |
| Sample API | 250m | 1 CPU | 256 Mi | 512 Mi |
| PGVector | 250m | 1 CPU | 512 Mi | 1 Gi |

## GPU requirements

The IBM Granite 4.0-H-Small model is a Mixture-of-Experts (MoE) architecture with 32B total parameters and 9B active parameters. With this design, the model can run on a single GPU with 24 GB of VRAM, such as the NVIDIA L4 available on AWS `g6.2xlarge` instances.

The vLLM serving configuration uses:

- `max-model-len: 8192` to balance context length with GPU memory usage
- `dtype: float16` for inference precision
- `gpu-memory-utilization: 0.9` to maximize available memory for KV cache

If you require a longer context window or plan to handle many concurrent requests, consider upgrading to a `g6.4xlarge` (48 GB VRAM) or `g5.4xlarge` instance.

## Cloud provider equivalents

| Cloud provider | GPU instance type | GPU | VRAM |
|----------------|-------------------|-----|------|
| AWS | g6.2xlarge | NVIDIA L4 | 24 GB |
| Azure | Standard_NC24ads_A100_v4 | NVIDIA A100 | 80 GB |
| GCP | g2-standard-8 | NVIDIA L4 | 24 GB |

## Storage requirements

The pattern uses persistent storage for the following components:

| Component | Storage class | Size | Purpose |
|-----------|---------------|------|---------|
| PGVector | gp3-csi | 5 Gi | Agent memory and vector embeddings |
| vLLM model cache | gp3-csi | 50 Gi | Downloaded model weights |

You can change the storage class by modifying `global.storageClass` in `values-global.yaml`.

## Scaling considerations

- **Concurrent users**: The default deployment supports approximately 5-10 concurrent chat sessions. To increase capacity, scale the bee-agent-service and agent-chat-ui replica counts in their respective Helm chart values.
- **Multiple models**: To serve additional models, deploy additional vLLM instances with separate GPU nodes. Each model requires its own GPU allocation.
- **Production workloads**: For production deployments, increase worker node count to 5 and consider dedicated GPU nodes for each vLLM instance.
