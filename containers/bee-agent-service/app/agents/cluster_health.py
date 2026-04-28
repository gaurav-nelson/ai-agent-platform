AGENT_NAME = "cluster-health"

from beeai_framework.agents.react import ReActAgent
from beeai_framework.memory import TokenMemory

from app.tools.kubernetes import (
    DescribeResourceTool,
    GetEventsTool,
    GetNodesTool,
    GetPodsTool,
)


def create_cluster_health_agent(llm):
    return ReActAgent(
        llm=llm,
        tools=[
            GetPodsTool(),
            GetNodesTool(),
            GetEventsTool(),
            DescribeResourceTool(),
        ],
        memory=TokenMemory(llm=llm, max_tokens=4096),
    )
