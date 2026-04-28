---
title: Ideas for customization
weight: 30
aliases: /ai-agent-platform/ideas-for-customization/
---

# Ideas for customizing the AI Agent Platform pattern

This pattern provides a building block for AI agent deployments. The following sections describe common ways to extend and adapt it for your use cases.

## Adding your own agents

The pattern uses an agent auto-discovery system. Each agent module must export two items:

- `AGENT_NAME`: A string that identifies the agent (for example, `"log-analyzer"`).
- `create_agent(llm)`: A function that accepts an LLM instance and returns a Bee AI Framework agent.

You can add agents in two ways:

### Option 1: Build into the container image

Create a new file in `containers/bee-agent-service/app/agents/`. For example, to create a log analysis agent:

1. Create `containers/bee-agent-service/app/agents/log_analyzer.py`:

   ```python
   AGENT_NAME = "log-analyzer"

   from beeai_framework.agents.react import ReActAgent
   from beeai_framework.memory import TokenMemory

   def create_agent(llm):
       return ReActAgent(
           llm=llm,
           tools=[your_log_tools],
           memory=TokenMemory(llm=llm, max_tokens=4096),
       )
   ```

2. Rebuild and push the bee-agent-service container image. The agent is discovered automatically at startup.

### Option 2: Mount as a ConfigMap (no image rebuild)

For lightweight agents that use only the dependencies available in the base image:

1. Create a ConfigMap containing your agent Python file:

   ```shell
   oc create configmap custom-agents --from-file=log_analyzer.py -n ai-agent
   ```

2. Enable custom agent loading in the Helm chart values by setting `customAgents.enabled` to `true` and `customAgents.configMapName` to `custom-agents`.

3. The service mounts the ConfigMap at `/custom-agents` and discovers the agent module at startup.

### Controlling which agents to load

Set the `ENABLED_AGENTS` environment variable to control agent loading:

- `""` (empty): Falls back to legacy `AGENT_MODE` behavior for backward compatibility.
- `"all"`: Loads every agent discovered in both the built-in and custom directories.
- `"cluster-health,log-analyzer"`: Loads only the specified agents by name.

## Creating custom tools

The Bee AI Framework provides a base `Tool` class that you can extend to create custom tools. Place new tools in `containers/bee-agent-service/app/tools/`.

Each tool requires:

- An input schema (Pydantic model) describing the parameters the agent can pass
- A `_run` method that executes the tool logic and returns a `StringToolOutput`
- A name and description that the LLM uses to decide when to call the tool

The existing Kubernetes tools in `containers/bee-agent-service/app/tools/kubernetes.py` provide a reference implementation.

## Connecting your own APIs

The API Explorer agent uses the `OpenAPITool.from_schema()` method to dynamically generate tools from any OpenAPI specification. To connect your own API:

1. Ensure your API exposes an OpenAPI specification at a known endpoint (for example, `/openapi.json`).
2. Deploy your API service in the `ai-agent` namespace or make it accessible from within the cluster.
3. Update the `SAMPLE_API_URL` environment variable in the bee-agent-service ConfigMap to point to your API.
4. The API Explorer agent automatically discovers and generates tools from the new specification.

You can also create multiple API-connected agents, each pointing to a different service.

## Changing the LLM

The pattern defaults to IBM Granite 4.0-H-Small. To use a different model:

1. Update `global.model.vllm` in `values-global.yaml` with the HuggingFace model ID (for example, `ibm-granite/granite-3.3-8b-instruct`).
2. Verify that the model fits within your GPU memory. The vLLM serving configuration in `charts/all/vllm-inference-service/values.yaml` controls `max-model-len` and `gpu-memory-utilization`.
3. If your model requires a gated access token, ensure the HuggingFace token in your secrets has the necessary permissions.

The Bee AI Framework works with any model that supports the OpenAI-compatible chat completions API. Models with native tool-calling support (such as Granite, Llama, or Mistral) produce the best agent performance.

## Adding RAG capabilities

The pattern includes PGVector for persistent agent memory. You can extend this to support retrieval-augmented generation (RAG):

1. Load your documents into PGVector by using an embedding model.
2. Create a retrieval tool that queries the vector database based on user questions.
3. Add the retrieval tool to an existing agent or create a new RAG-enabled agent.

The Bee AI Framework includes RAG utilities in the `beeai-framework[rag]` package extra.

## Integrating with external services

You can extend agents to interact with external services such as:

- **Ticketing systems** (Jira, ServiceNow) - Create tools that open, update, or query tickets
- **Monitoring platforms** (Prometheus, Datadog) - Create tools that query metrics and alert status
- **CI/CD pipelines** (Tekton, Jenkins) - Create tools that trigger builds or check pipeline status
- **Messaging** (Slack, Microsoft Teams) - Create tools that send notifications or summaries

Each integration follows the same pattern: create a custom tool class, register it with an agent, and rebuild the container.

## Modifying the GitOps configuration

You can adjust the ArgoCD application settings by modifying the Helm chart values:

- **Add new applications**: Edit `values-hub.yaml` and add entries under the `applications` section.
- **Change sync policies**: Modify `global.options.syncPolicy` in `values-global.yaml`.
- **Adjust sync-wave ordering**: Update the `argocd.io/sync-wave` annotations in individual chart templates to control deployment order.

## Next steps

- [Getting started](../getting-started) - Deploy the base pattern
- [Troubleshooting](../troubleshooting) - Resolve common issues
