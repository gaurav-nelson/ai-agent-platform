import asyncio
from typing import Any

from kubernetes import client, config
from pydantic import BaseModel, Field

from beeai_framework.tools.tool import StringToolOutput, Tool, ToolRunOptions
from beeai_framework.context import RunContext


def _load_k8s_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


_load_k8s_config()
_core_v1 = client.CoreV1Api()
_apps_v1 = client.AppsV1Api()


class GetPodsInput(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace to list pods from")
    label_selector: str = Field(default="", description="Optional label selector to filter pods")


class GetPodsTool(Tool[GetPodsInput, ToolRunOptions, StringToolOutput]):
    name = "GetPods"
    description = "List pods in a Kubernetes namespace with their name, status, and restart count"
    input_schema = GetPodsInput

    async def _run(self, input: GetPodsInput, options: ToolRunOptions | None, context: RunContext) -> StringToolOutput:
        pods = await asyncio.to_thread(
            _core_v1.list_namespaced_pod,
            namespace=input.namespace,
            label_selector=input.label_selector,
        )
        lines = []
        for pod in pods.items:
            name = pod.metadata.name
            phase = pod.status.phase
            restarts = sum(cs.restart_count for cs in (pod.status.container_statuses or []))
            lines.append(f"{name}  Status={phase}  Restarts={restarts}")
        if not lines:
            return StringToolOutput(f"No pods found in namespace '{input.namespace}'")
        return StringToolOutput("\n".join(lines))


class GetNodesInput(BaseModel):
    pass


class GetNodesTool(Tool[GetNodesInput, ToolRunOptions, StringToolOutput]):
    name = "GetNodes"
    description = "List all Kubernetes nodes with their status, roles, and resource capacity"
    input_schema = GetNodesInput

    async def _run(self, input: GetNodesInput, options: ToolRunOptions | None, context: RunContext) -> StringToolOutput:
        nodes = await asyncio.to_thread(_core_v1.list_node)
        lines = []
        for node in nodes.items:
            name = node.metadata.name
            conditions = {c.type: c.status for c in (node.status.conditions or [])}
            ready = conditions.get("Ready", "Unknown")
            roles = [k.split("/")[-1] for k in (node.metadata.labels or {}) if k.startswith("node-role.kubernetes.io/")]
            cpu = node.status.capacity.get("cpu", "?")
            mem = node.status.capacity.get("memory", "?")
            gpu = node.status.capacity.get("nvidia.com/gpu", "0")
            lines.append(f"{name}  Ready={ready}  Roles={','.join(roles) or 'worker'}  CPU={cpu}  Memory={mem}  GPU={gpu}")
        return StringToolOutput("\n".join(lines))


class GetEventsInput(BaseModel):
    namespace: str = Field(default="default", description="Kubernetes namespace to list events from")
    limit: int = Field(default=20, description="Maximum number of recent events to return")


class GetEventsTool(Tool[GetEventsInput, ToolRunOptions, StringToolOutput]):
    name = "GetEvents"
    description = "List recent Kubernetes events in a namespace, useful for debugging issues"
    input_schema = GetEventsInput

    async def _run(self, input: GetEventsInput, options: ToolRunOptions | None, context: RunContext) -> StringToolOutput:
        events = await asyncio.to_thread(
            _core_v1.list_namespaced_event,
            namespace=input.namespace,
            limit=input.limit,
        )
        lines = []
        for event in events.items:
            kind = event.involved_object.kind or "?"
            obj_name = event.involved_object.name or "?"
            reason = event.reason or "?"
            message = event.message or ""
            ev_type = event.type or "Normal"
            lines.append(f"[{ev_type}] {kind}/{obj_name}: {reason} - {message}")
        if not lines:
            return StringToolOutput(f"No events found in namespace '{input.namespace}'")
        return StringToolOutput("\n".join(lines))


class DescribeResourceInput(BaseModel):
    resource_type: str = Field(description="Type of resource: pod, node, deployment, service")
    name: str = Field(description="Name of the resource to describe")
    namespace: str = Field(default="default", description="Namespace of the resource (not used for nodes)")


class DescribeResourceTool(Tool[DescribeResourceInput, ToolRunOptions, StringToolOutput]):
    name = "DescribeResource"
    description = "Get detailed information about a specific Kubernetes resource (pod, node, deployment, or service)"
    input_schema = DescribeResourceInput

    async def _run(self, input: DescribeResourceInput, options: ToolRunOptions | None, context: RunContext) -> StringToolOutput:
        rt = input.resource_type.lower()
        try:
            if rt == "pod":
                obj = await asyncio.to_thread(_core_v1.read_namespaced_pod, input.name, input.namespace)
                return StringToolOutput(self._format_pod(obj))
            elif rt == "node":
                obj = await asyncio.to_thread(_core_v1.read_node, input.name)
                return StringToolOutput(self._format_node(obj))
            elif rt == "deployment":
                obj = await asyncio.to_thread(_apps_v1.read_namespaced_deployment, input.name, input.namespace)
                return StringToolOutput(self._format_deployment(obj))
            elif rt == "service":
                obj = await asyncio.to_thread(_core_v1.read_namespaced_service, input.name, input.namespace)
                return StringToolOutput(self._format_service(obj))
            else:
                return StringToolOutput(f"Unsupported resource type: {rt}. Supported: pod, node, deployment, service")
        except client.ApiException as e:
            return StringToolOutput(f"Error: {e.reason} (status {e.status})")

    def _format_pod(self, pod: Any) -> str:
        containers = []
        for cs in (pod.status.container_statuses or []):
            containers.append(f"  {cs.name}: ready={cs.ready}, restarts={cs.restart_count}")
        return (
            f"Pod: {pod.metadata.name}\n"
            f"Namespace: {pod.metadata.namespace}\n"
            f"Phase: {pod.status.phase}\n"
            f"Node: {pod.spec.node_name}\n"
            f"Containers:\n" + "\n".join(containers)
        )

    def _format_node(self, node: Any) -> str:
        conditions = "\n".join(f"  {c.type}: {c.status}" for c in (node.status.conditions or []))
        return (
            f"Node: {node.metadata.name}\n"
            f"CPU: {node.status.capacity.get('cpu', '?')}\n"
            f"Memory: {node.status.capacity.get('memory', '?')}\n"
            f"GPU: {node.status.capacity.get('nvidia.com/gpu', '0')}\n"
            f"Conditions:\n{conditions}"
        )

    def _format_deployment(self, dep: Any) -> str:
        return (
            f"Deployment: {dep.metadata.name}\n"
            f"Namespace: {dep.metadata.namespace}\n"
            f"Replicas: {dep.status.ready_replicas or 0}/{dep.spec.replicas}\n"
            f"Available: {dep.status.available_replicas or 0}\n"
            f"Updated: {dep.status.updated_replicas or 0}"
        )

    def _format_service(self, svc: Any) -> str:
        ports = ", ".join(f"{p.port}/{p.protocol}" for p in (svc.spec.ports or []))
        return (
            f"Service: {svc.metadata.name}\n"
            f"Namespace: {svc.metadata.namespace}\n"
            f"Type: {svc.spec.type}\n"
            f"ClusterIP: {svc.spec.cluster_ip}\n"
            f"Ports: {ports}"
        )
