from app.tools.kubernetes import (
    DescribeResourceTool,
    GetEventsTool,
    GetNodesTool,
    GetPodsTool,
)
from beeai_framework.agents.react import ReActAgent
from beeai_framework.memory import TokenMemory

AGENT_NAME = "cluster-health"


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
