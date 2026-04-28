import logging
import os
import subprocess

import pytest
from ocp_resources.pod import Pod
from ocp_resources.route import Route

logger = logging.getLogger(__name__)

is_addon_mode = os.environ.get("PATTERN_MODE") == "addon"

"""
Validate AI agent-specific services for the AI Agent GitOps pattern.
Checks vLLM inference, bee-agent-service, sample-api, and agent-chat-ui.
"""


@pytest.mark.validate_vllm_serving
@pytest.mark.skipif(is_addon_mode, reason="vLLM not deployed in add-on mode")
def test_validate_vllm_serving(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))

    vllm_pods = [
        p for p in pods
        if "vllm" in p.instance.metadata.name.lower()
        and p.instance.status.phase == "Running"
    ]

    logger.info(f"vLLM pods running: {len(vllm_pods)}")
    for pod in vllm_pods:
        logger.info(f"  {pod.instance.metadata.name}: {pod.instance.status.phase}")

    assert len(vllm_pods) >= 1, (
        "No running vLLM inference pod found in ai-agent namespace"
    )


@pytest.mark.validate_bee_agent_service
def test_validate_bee_agent_service(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))

    agent_pods = [
        p for p in pods
        if "bee-agent" in p.instance.metadata.name.lower()
        and p.instance.status.phase == "Running"
    ]

    logger.info(f"Bee agent service pods running: {len(agent_pods)}")
    assert len(agent_pods) >= 1, (
        "No running bee-agent-service pod found in ai-agent namespace"
    )


@pytest.mark.validate_sample_api
def test_validate_sample_api(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))

    api_pods = [
        p for p in pods
        if "sample-api" in p.instance.metadata.name.lower()
        and p.instance.status.phase == "Running"
    ]

    logger.info(f"Sample API pods running: {len(api_pods)}")
    assert len(api_pods) >= 1, (
        "No running sample-api pod found in ai-agent namespace"
    )


@pytest.mark.validate_agent_chat_ui
def test_validate_agent_chat_ui(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))

    ui_pods = [
        p for p in pods
        if "agent-chat-ui" in p.instance.metadata.name.lower()
        and p.instance.status.phase == "Running"
    ]

    logger.info(f"Agent chat UI pods running: {len(ui_pods)}")
    assert len(ui_pods) >= 1, (
        "No running agent-chat-ui pod found in ai-agent namespace"
    )


@pytest.mark.validate_pgvector
def test_validate_pgvector(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))

    pg_pods = [
        p for p in pods
        if "pgvector" in p.instance.metadata.name.lower()
        and p.instance.status.phase == "Running"
    ]

    logger.info(f"PGVector pods running: {len(pg_pods)}")
    assert len(pg_pods) >= 1, (
        "No running pgvector pod found in ai-agent namespace"
    )


@pytest.mark.validate_bee_agent_health_endpoint
def test_validate_bee_agent_health_endpoint(openshift_dyn_client):
    routes = list(
        Route.get(dyn_client=openshift_dyn_client, namespace="ai-agent")
    )

    agent_route = None
    for r in routes:
        if r.instance.metadata.name == "bee-agent-service":
            agent_route = r
            break

    assert agent_route is not None, "bee-agent-service route not found"

    host = agent_route.instance.spec.host
    result = subprocess.run(
        ["curl", "-sk", f"https://{host}/health", "--max-time", "10"],
        capture_output=True,
        text=True,
    )

    logger.info(f"Agent health endpoint response: {result.stdout}")
    assert result.returncode == 0, f"Health endpoint unreachable: {result.stderr}"
    assert "healthy" in result.stdout.lower(), (
        f"Health endpoint did not return healthy status: {result.stdout}"
    )


@pytest.mark.validate_bee_agent_lists_agents
def test_validate_bee_agent_lists_agents(openshift_dyn_client):
    routes = list(
        Route.get(dyn_client=openshift_dyn_client, namespace="ai-agent")
    )

    agent_route = None
    for r in routes:
        if r.instance.metadata.name == "bee-agent-service":
            agent_route = r
            break

    assert agent_route is not None, "bee-agent-service route not found"

    host = agent_route.instance.spec.host
    result = subprocess.run(
        ["curl", "-sk", f"https://{host}/agents", "--max-time", "10"],
        capture_output=True,
        text=True,
    )

    logger.info(f"Agent list response: {result.stdout}")
    assert result.returncode == 0, f"Agents endpoint unreachable: {result.stderr}"
    assert "cluster-health" in result.stdout, (
        f"cluster-health agent not found in response: {result.stdout}"
    )
