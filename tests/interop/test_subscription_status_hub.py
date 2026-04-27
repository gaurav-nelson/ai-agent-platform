import logging
import os

import pytest
from validatedpatterns_tests.interop import subscription

logger = logging.getLogger(__name__)

"""
Validate that the expected operator subscriptions are present and healthy
on the hub cluster for the AI Agent GitOps pattern.
"""


@pytest.mark.subscription_status_hub
def test_subscription_status_hub(openshift_dyn_client):
    expected_subs = {
        "openshift-gitops-operator": ["openshift-gitops-operator"],
        "openshift-nfd": ["nfd"],
        "nvidia-gpu-operator": ["gpu-operator-certified"],
        "openshift-serverless": ["serverless-operator"],
        "openshift-operators": ["servicemeshoperator"],
        "redhat-ods-operator": ["rhods-operator"],
    }

    operator_versions = []
    missing_subs = []

    for namespace, subs in expected_subs.items():
        for sub_name in subs:
            sub_status = subscription.subscription_status(
                openshift_dyn_client, sub_name, namespace
            )
            if sub_status:
                operator_versions.append(f"{sub_name}: {sub_status}")
                logger.info(f"Subscription {sub_name} in {namespace}: {sub_status}")
            else:
                missing_subs.append(f"{sub_name} in {namespace}")
                logger.error(f"Subscription {sub_name} NOT FOUND in {namespace}")

    if operator_versions:
        logger.info("Installed operator versions:")
        for ov in operator_versions:
            logger.info(f"  {ov}")

    assert not missing_subs, f"Missing subscriptions: {missing_subs}"
