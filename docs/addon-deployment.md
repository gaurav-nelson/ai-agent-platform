---
title: Deploying as an add-on
weight: 15
aliases: /ai-agent-platform/addon-deployment/
---

# Deploying the AI Agent Platform as an add-on

You can install the AI Agent Platform alongside an existing validated pattern on the same OpenShift cluster. In add-on mode, the pattern deploys only the AI agent components and relies on the host pattern for shared infrastructure such as Vault, external secrets operators, and GPU nodes.

The validated patterns framework natively supports multiple patterns on a single cluster. Each pattern creates its own `Pattern` custom resource and manages its own namespaces, while sharing the Patterns Operator and ArgoCD instance.

## Prerequisites

- An OpenShift cluster with an existing validated pattern already deployed (for example, [Portworx DR](https://validatedpatterns.io/patterns/portworx-dr/) or [Multicloud GitOps](https://validatedpatterns.io/patterns/multicloud-gitops/))
- The existing pattern provides:
  - HashiCorp Vault for secrets management
  - An external secrets operator
  - GPU nodes (if you plan to run vLLM locally)
- Cluster-admin access to the OpenShift cluster
- An accessible LLM endpoint (either from the host pattern or an external service)
- [Validated patterns tooling dependencies](https://validatedpatterns.io/learn/quickstart/) installed on your workstation
- The `oc` CLI installed and authenticated to your cluster

## Procedure

1. Fork the [ai-agent-platform](https://github.com/validatedpatterns/ai-agent-platform) repository on GitHub.

2. Clone your forked repository:

   ```shell
   git clone git@github.com:<your-organization>/ai-agent-platform.git
   ```

3. Change to the pattern directory:

   ```shell
   cd ai-agent-platform
   ```

4. Configure add-on mode by editing `values-global.yaml`. Change `clusterGroupName` from `hub` to `addon` and set the LLM endpoint URL:

   ```yaml
   global:
     pattern: ai-agent-platform
     agent:
       mode: both
       enabledAgents: "all"
       customAgentsDir: ""

   main:
     clusterGroupName: addon
   ```

5. Set the LLM endpoint. If the host pattern does not provide a vLLM instance, point to an external LLM service by creating an override file at `overrides/values-addon.yaml`:

   ```yaml
   beeAgentService:
     env:
       VLLM_BASE_URL: "https://your-llm-endpoint/v1"
       OPENAI_API_KEY: "your-api-key"
   ```

   If the host pattern already runs a vLLM instance, use its in-cluster service URL instead.

6. Deploy the pattern:

   ```shell
   ./pattern.sh make install
   ```

   This creates a `Pattern/ai-agent-platform` custom resource alongside the existing pattern. ArgoCD deploys only the AI agent components into the `ai-agent` namespace.

## What gets deployed

In add-on mode, the pattern deploys only the following components:

| Component | Description |
|-----------|-------------|
| Bee agent service | Agent orchestration service with auto-discovery |
| Agent chat UI | Gradio-based web interface |
| PGVector | PostgreSQL with vector extensions for agent memory |
| Sample API | Demo REST service for the API Explorer agent |

The following components are **not** deployed in add-on mode because they are expected from the host pattern:

- Vault and external secrets operator
- NFD and NVIDIA GPU Operator
- OpenShift AI
- vLLM inference service
- Monitoring stack

## Adding custom agents for your pattern

When running as an add-on, you typically want agents that interact with the host pattern's services. For example, if you are running alongside the Portworx DR pattern, you might create a DR operations agent that queries Portworx storage cluster status and triggers Ansible Automation Platform playbooks.

See [Ideas for customization](../ideas-for-customization) for instructions on creating custom agents using the plugin system.

## Verifying the deployment

1. Check that all pods in the `ai-agent` namespace are running:

   ```shell
   oc get pods -n ai-agent
   ```

   You should see pods for bee-agent-service, agent-chat-ui, pgvector, and sample-api.

2. Verify the bee-agent-service health endpoint:

   ```shell
   curl -sk "https://$(oc get route bee-agent-service -n ai-agent -o jsonpath='{.spec.host}')/health"
   ```

3. Verify that both patterns are running independently:

   ```shell
   oc get patterns -n openshift-operators
   ```

   You should see both the host pattern and `ai-agent-platform` listed.

## Removing the add-on

To remove the AI Agent Platform without affecting the host pattern, delete the Pattern custom resource:

```shell
oc delete pattern ai-agent-platform -n openshift-operators
```

This removes only the AI agent components. The host pattern and its resources remain untouched.

## Next steps

- [Ideas for customization](../ideas-for-customization) - Create custom agents for your use case
- [Troubleshooting](../troubleshooting) - Resolve common issues
