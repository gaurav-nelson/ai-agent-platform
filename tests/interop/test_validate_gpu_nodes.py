import logging

import pytest
from ocp_resources.machine_set import MachineSet
from ocp_resources.node import Node
from ocp_resources.pod import Pod

logger = logging.getLogger(__name__)

"""
Validate GPU node provisioning for the AI Agent GitOps pattern.
"""


@pytest.mark.validate_gpu_machineset
def test_validate_gpu_nodes(openshift_dyn_client):
    gpu_machinesets = []

    for ms in MachineSet.get(
        dyn_client=openshift_dyn_client,
        namespace="openshift-machine-api",
    ):
        ms_name = ms.instance.metadata.name
        if "gpu" in ms_name.lower() or "nvidia" in ms_name.lower():
            gpu_machinesets.append(ms)
            logger.info(f"Found GPU MachineSet: {ms_name}")

            spec = ms.instance.spec.template.spec
            provider_spec = spec.providerSpec.value

            if hasattr(provider_spec, "instanceType"):
                logger.info(f"  Instance type: {provider_spec.instanceType}")
            elif hasattr(provider_spec, "vmSize"):
                logger.info(f"  VM size: {provider_spec.vmSize}")

            taints = spec.get("taints", [])
            if taints:
                for taint in taints:
                    logger.info(f"  Taint: {taint.key}={taint.get('value', '')}:{taint.effect}")

            labels = spec.metadata.get("labels", {})
            for key, val in labels.items():
                if "gpu" in key.lower() or "nvidia" in key.lower() or "odh" in key.lower():
                    logger.info(f"  Label: {key}={val}")

    assert len(gpu_machinesets) > 0, (
        "No GPU MachineSet found. Run 'make create-gpu-machineset' to provision GPU nodes."
    )


@pytest.mark.validate_gpu_node_role_labels_pods
def test_validate_gpu_node_role_labels_pods(openshift_dyn_client):
    gpu_nodes = []
    for node in Node.get(dyn_client=openshift_dyn_client):
        labels = node.instance.metadata.labels or {}
        if labels.get("nvidia.com/gpu.present") == "true":
            gpu_nodes.append(node.instance.metadata.name)
            logger.info(f"GPU node found: {node.instance.metadata.name}")

            has_worker = "node-role.kubernetes.io/worker" in labels
            has_odh = "node-role.kubernetes.io/odh-notebook" in labels
            logger.info(f"  worker role: {has_worker}, odh-notebook role: {has_odh}")

    nvidia_pods = list(
        Pod.get(
            dyn_client=openshift_dyn_client,
            namespace="nvidia-gpu-operator",
        )
    )
    running_pods = [
        p for p in nvidia_pods
        if p.instance.status.phase == "Running"
    ]

    logger.info(f"NVIDIA GPU operator pods: {len(running_pods)} running out of {len(nvidia_pods)} total")

    assert len(running_pods) >= 4, (
        f"Expected at least 4 running NVIDIA pods, found {len(running_pods)}"
    )
