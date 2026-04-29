import httpx
from app.config import settings
from beeai_framework.agents.react import ReActAgent
from beeai_framework.memory import TokenMemory
from beeai_framework.tools.openapi import OpenAPITool

AGENT_NAME = "api-explorer"


def create_api_explorer_agent(llm):
    spec = httpx.get(f"{settings.SAMPLE_API_URL}/openapi.json").json()
    tools = OpenAPITool.from_schema(spec, api_url=settings.SAMPLE_API_URL)

    return ReActAgent(
        llm=llm,
        tools=tools,
        memory=TokenMemory(llm=llm, max_tokens=4096),
    )
