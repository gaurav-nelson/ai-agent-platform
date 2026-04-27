---
title: Getting started
weight: 10
aliases: /ai-agent-platform/getting-started/
---

# Deploying the AI Agent Platform pattern

## Prerequisites

- An OpenShift cluster running version 4.12 or later
  - To create an OpenShift cluster, go to the [Red Hat Hybrid Cloud console](https://console.redhat.com/) and select **Services -> Containers -> Create cluster**.
  - The cluster must have a dynamic `StorageClass` to provision `PersistentVolumes`. The default is `gp3-csi` for AWS.
  - Review the [cluster sizing](../cluster-sizing) requirements.
- Cluster-admin access to the OpenShift cluster
- A [HuggingFace account](https://huggingface.co/) with an API token that has access to the [IBM Granite 4.0-H-Small](https://huggingface.co/ibm-granite/granite-4.0-h-small) model
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

4. Copy the secrets template and add your HuggingFace token:

   ```shell
   cp values-secret.yaml.template ~/values-secret-ai-agent-platform.yaml
   ```

   Edit `~/values-secret-ai-agent-platform.yaml` and set the `hftoken` field under the `hfmodel` secret:

   ```yaml
   secrets:
     - name: hfmodel
       fields:
         - name: hftoken
           value: hf_your_token_here
   ```

5. Deploy the pattern:

   ```shell
   ./pattern.sh make install
   ```

   This command installs the validated patterns operator, which then deploys all components through ArgoCD. The initial deployment takes approximately 15-20 minutes.

6. Provision a GPU node for model serving:

   ```shell
   make create-gpu-machineset
   ```

   This command creates an AWS `g6.2xlarge` MachineSet (or equivalent for your cloud provider) with the NVIDIA GPU Operator configured. The GPU node takes approximately 10-15 minutes to become ready.

   > **Note:** For Azure deployments, the Makefile automatically selects the appropriate GPU instance type. See [GPU provisioning](../GPU_provisioning.md) for details on supported cloud providers.

## Verifying the deployment

After all ArgoCD applications report a **Healthy** status, verify the deployment:

1. Check that all pods in the `ai-agent` namespace are running:

   ```shell
   oc get pods -n ai-agent
   ```

   You should see pods for vLLM, PGVector, bee-agent-service, sample-api, and agent-chat-ui.

2. Verify the vLLM inference service is serving the model:

   ```shell
   oc logs -n ai-agent -l app=vllm --tail=20
   ```

   Look for a message indicating the model loaded successfully.

3. Check the bee-agent-service health endpoint:

   ```shell
   curl -sk "https://$(oc get route bee-agent-service -n ai-agent -o jsonpath='{.spec.host}')/health"
   ```

4. Access the Agent Chat UI by navigating to the route URL:

   ```shell
   oc get route agent-chat-ui -n ai-agent -o jsonpath='{.spec.host}'
   ```

   Open this URL in your browser to interact with the demo agents.

## Accessing the monitoring dashboard

The pattern deploys a Grafana dashboard with agent metrics. Access it through the OpenShift console:

1. In the OpenShift web console, look for the **AI Agent Monitoring** link in the application launcher menu.
2. The dashboard displays agent request rates, tool call distribution, response times, and token usage.

## Next steps

- [Ideas for customization](../ideas-for-customization) - Add your own agents, tools, and APIs
- [Troubleshooting](../troubleshooting) - Resolve common deployment issues
