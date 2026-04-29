import logging
import os
import subprocess

import pytest
from ocp_resources.pod import Pod
from ocp_resources.route import Route
from validatedpatterns_tests.interop import application, components

logger = logging.getLogger(__name__)

is_addon_mode = os.environ.get("PATTERN_MODE") == "addon"

"""
Validate hub site components for the AI Agent GitOps pattern.
Checks pod health, routes, ArgoCD apps, GPU config, and agent services.
"""


@pytest.mark.validate_hub_site_components
def test_validate_hub_site_components(openshift_dyn_client):
    logger.info("--- AI Agent GitOps Hub Site Component Validation ---")

    namespaces_to_check = ["ai-agent", "nvidia-gpu-operator", "agent-monitoring"]
    for ns in namespaces_to_check:
        pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace=ns))
        logger.info(f"Namespace {ns}: {len(pods)} pods")
        for pod in pods:
            logger.info(
                f"  {pod.instance.metadata.name}: {pod.instance.status.phase}"
            )


@pytest.mark.validate_hub_site_reachable
def test_validate_hub_site_reachable(openshift_dyn_client):
    result = components.dump_openshift_version()
    logger.info(f"OpenShift version: {result}")


@pytest.mark.check_pod_status_hub
def test_check_pod_status(openshift_dyn_client):
    bad_pods = []
    namespaces = ["nvidia-gpu-operator", "ai-agent"]

    for ns in namespaces:
        for pod in Pod.get(dyn_client=openshift_dyn_client, namespace=ns):
            phase = pod.instance.status.phase
            name = pod.instance.metadata.name

            if phase in ("Succeeded", "Completed"):
                continue
            if phase != "Running":
                bad_pods.append(f"{ns}/{name} ({phase})")
                logger.error(f"Pod not running: {ns}/{name} phase={phase}")

    assert not bad_pods, f"Unhealthy pods found: {bad_pods}"


@pytest.mark.check_pod_count_hub
def test_check_pod_count_hub(openshift_dyn_client):
    pods = list(Pod.get(dyn_client=openshift_dyn_client, namespace="ai-agent"))
    active_pods = [
        p for p in pods
        if p.instance.status.phase not in ("Succeeded", "Failed")
    ]
    logger.info(f"ai-agent namespace: {len(active_pods)} active pods")

    min_pods = 4 if is_addon_mode else 5
    assert len(active_pods) >= min_pods, (
        f"Expected at least {min_pods} active pods in ai-agent namespace, "
        f"found {len(active_pods)}"
    )


@pytest.mark.validate_argocd_reachable_hub_site
def test_validate_argocd_reachable_hub_site(openshift_dyn_client):
    result = application.argocd_route_check(openshift_dyn_client)
    logger.info(f"ArgoCD route check: {result}")
    assert result, "ArgoCD route is not reachable"


@pytest.mark.validate_agent_ui_route
def test_validate_agent_ui_route(openshift_dyn_client):
    routes = list(
        Route.get(dyn_client=openshift_dyn_client, namespace="ai-agent")
    )
    route_names = [r.instance.metadata.name for r in routes]
    logger.info(f"Routes in ai-agent namespace: {route_names}")

    assert "agent-chat-ui" in route_names, (
        f"agent-chat-ui route not found. Available routes: {route_names}"
    )

    assert "bee-agent-service" in route_names, (
        f"bee-agent-service route not found. Available routes: {route_names}"
    )


@pytest.mark.validate_nodefeaturediscovery
@pytest.mark.skipif(is_addon_mode, reason="NFD not deployed in add-on mode")
def test_validate_nodefeaturediscovery(openshift_dyn_client):
    result = subprocess.run(
        ["oc", "get", "nodefeaturediscovery", "nfd-instance", "-n", "openshift-nfd"],
        capture_output=True,
        text=True,
    )
    logger.info(f"NFD instance check: {result.stdout}")
    assert result.returncode == 0, (
        f"NodeFeatureDiscovery nfd-instance not found: {result.stderr}"
    )


@pytest.mark.validate_gpu_clusterpolicy
@pytest.mark.skipif(is_addon_mode, reason="GPU not deployed in add-on mode")
def test_validate_gpu_clusterpolicy(openshift_dyn_client):
    result = subprocess.run(
        [
            "oc", "get", "clusterpolicy",
            "ai-agent-platform-nvidia-gpu-config-gpu-cluster-policy",
            "-o", "json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"GPU ClusterPolicy not found: {result.stderr}"
    )
    logger.info("GPU ClusterPolicy found and accessible")


@pytest.mark.validate_argocd_applications_health_hub_site
def test_validate_argocd_applications_health_hub_site(openshift_dyn_client):
    unhealthy = []

    for ns in ["openshift-gitops", "ai-agent-platform-hub"]:
        apps = application.get_argocd_application_status(
            openshift_dyn_client, ns
        )
        if apps:
            for app_name, health in apps.items():
                logger.info(f"ArgoCD app {ns}/{app_name}: {health}")
                if health not in ("Healthy", "Progressing"):
                    unhealthy.append(f"{ns}/{app_name}: {health}")

    assert not unhealthy, f"Unhealthy ArgoCD applications: {unhealthy}"
