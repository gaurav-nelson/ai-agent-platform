---
title: Troubleshooting
weight: 40
aliases: /ai-agent-platform/troubleshooting/
---

# Troubleshooting the AI Agent Platform pattern

## Checking the deployment status

Verify that all ArgoCD applications are healthy:

```shell
oc get applications -n openshift-gitops
oc get applications -n ai-agent-platform-hub
```

All applications should show **Healthy** in the `HEALTH STATUS` column and **Synced** in the `SYNC STATUS` column.

To check for pods that are not running:

```shell
oc get pods -A | grep -v Running | grep -v Completed
```

## vLLM inference service issues

### The vLLM pod is in Pending state

The vLLM pod requires a GPU node. Verify that a GPU node exists and is ready:

```shell
oc get nodes -l nvidia.com/gpu.present=true
```

If no GPU nodes are listed, provision one:

```shell
make create-gpu-machineset
```

The GPU node takes approximately 10-15 minutes to become available after the MachineSet is created.

### The vLLM pod reports an out-of-memory error

The IBM Granite 4.0-H-Small model requires approximately 18-20 GB of GPU memory. If you see CUDA out-of-memory errors:

1. Reduce `max-model-len` in `charts/all/vllm-inference-service/values.yaml`:

   ```yaml
   maxModelLen: 4096
   ```

2. Verify that `gpu-memory-utilization` is set to `0.9` or lower.

3. If the problem persists, upgrade to a GPU instance with more VRAM (for example, `g5.4xlarge` on AWS).

### The model download fails

Verify that your HuggingFace token is correctly configured:

```shell
oc get secret hfmodel -n ai-agent -o jsonpath='{.data.hftoken}' | base64 -d
```

Ensure the token has read access to the [IBM Granite 4.0-H-Small](https://huggingface.co/ibm-granite/granite-4.0-h-small) model on HuggingFace.

## Bee agent service issues

### The bee-agent-service pod fails to start

Check the pod logs for error details:

```shell
oc logs -n ai-agent -l app=bee-agent-service --tail=50
```

Common causes include:

- **vLLM not ready**: The bee-agent-service attempts to connect to vLLM on startup. Ensure the vLLM pod is running and the model is loaded before the agent service starts. The sync-wave ordering (vLLM at wave 20, bee-agent at wave 30) handles this automatically during initial deployment.
- **RBAC issues**: The bee-agent-service requires a ClusterRole with read access to Kubernetes resources. Verify the ClusterRoleBinding exists:

  ```shell
  oc get clusterrolebinding bee-agent-read-binding
  ```

### The health endpoint returns an unhealthy status

```shell
curl -sk "https://$(oc get route bee-agent-service -n ai-agent -o jsonpath='{.spec.host}')/health"
```

If the response does not contain "healthy", check whether all agents registered successfully:

```shell
curl -sk "https://$(oc get route bee-agent-service -n ai-agent -o jsonpath='{.spec.host}')/agents"
```

The response should list both `cluster-health` and `api-explorer` agents.

### Agent responses are slow or time out

Agent response times depend on the vLLM inference speed. ReAct agents make multiple LLM calls per request (one for each reasoning step). Typical response times are 15-60 seconds depending on the complexity of the query.

To improve performance:

- Ensure the GPU node has sufficient resources and is not shared with other GPU workloads.
- Reduce `max-model-len` to free GPU memory for larger batch sizes.
- Consider upgrading to a faster GPU instance type.

## Sample API issues

### The API Explorer agent cannot connect to the sample API

Verify the sample-api service is running and accessible:

```shell
oc get svc sample-api -n ai-agent
curl -sk "http://sample-api.ai-agent.svc.cluster.local:8080/health"
```

If the service is not reachable from within the cluster, check the service endpoints:

```shell
oc get endpoints sample-api -n ai-agent
```

## PGVector issues

### PGVector pod is in CrashLoopBackOff

Check the pod logs:

```shell
oc logs -n ai-agent -l app=pgvector --tail=30
```

Common causes include:

- **Persistent volume not provisioned**: Verify the storage class exists and can provision volumes:

  ```shell
  oc get sc gp3-csi
  oc get pvc -n ai-agent
  ```

- **Insufficient storage**: The default PVC size is 5 Gi. If the database grows beyond this, increase the PVC size in `charts/all/pgvector/values.yaml`.

## GPU and NVIDIA operator issues

### NVIDIA GPU operator pods are not running

Verify the NFD and GPU operator subscriptions:

```shell
oc get csv -n openshift-nfd
oc get csv -n nvidia-gpu-operator
```

Check that the NodeFeatureDiscovery instance exists:

```shell
oc get nodefeaturediscovery nfd-instance -n openshift-nfd
```

Check the GPU ClusterPolicy:

```shell
oc get clusterpolicy
```

### GPU node is not detected

After provisioning a GPU MachineSet, verify the node has the correct labels:

```shell
oc get nodes -l nvidia.com/gpu.present=true --show-labels
```

The node should have both `node-role.kubernetes.io/worker` and `nvidia.com/gpu.present=true` labels.

## Monitoring issues

### Grafana dashboard shows no data

Verify the ServiceMonitor resources exist and target the correct services:

```shell
oc get servicemonitor -n agent-monitoring
```

Check that the bee-agent-service and agent-chat-ui pods expose metrics on port 8000:

```shell
oc port-forward -n ai-agent svc/bee-agent-service 8000:8000
curl http://localhost:8000/metrics
```

## Known issues

- The vLLM pod restart policy may cause brief service interruptions if the GPU node experiences memory pressure. Monitor GPU utilization through the Grafana dashboard.
- On Azure deployments, the GPU MachineSet template uses a different instance type. Run `make create-gpu-machineset` and the Makefile automatically detects the cloud provider.

## Next steps

- [Getting started](../getting-started) - Review deployment steps
- [Cluster sizing](../cluster-sizing) - Verify resource requirements
