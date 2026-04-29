import logging
import time

import uvicorn
from app.config import settings
from app.metrics import (
    agent_request_duration_seconds,
    agent_requests_total,
    start_metrics_server,
)
from beeai_framework.adapters.openai.backend.chat import OpenAIChatModel
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bee Agent Service",
    description="AI Agent Platform powered by Bee AI Framework and IBM Granite",
    version="1.0.0",
)

llm = None
agents = {}


class ChatRequest(BaseModel):
    message: str
    agent: str = "cluster-health"


class ChatResponse(BaseModel):
    response: str
    agent: str
    duration_seconds: float


@app.on_event("startup")
async def startup():
    global llm, agents

    logger.info(
        f"Connecting to LLM at {settings.VLLM_BASE_URL} with model {settings.MODEL_NAME}"
    )
    llm = OpenAIChatModel(
        model_id=settings.MODEL_NAME,
        base_url=settings.VLLM_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
    )

    from app.agent_loader import discover_agents

    agents = discover_agents(
        enabled=settings.ENABLED_AGENTS,
        custom_dir=settings.CUSTOM_AGENTS_DIR,
        llm=llm,
        legacy_mode=settings.AGENT_MODE,
    )

    start_metrics_server()
    logger.info(f"Agent service ready. Available agents: {list(agents.keys())}")


@app.get("/health")
def health():
    return {"status": "healthy", "agents": list(agents.keys())}


@app.get("/agents")
def list_agents():
    return {"agents": list(agents.keys())}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent_name = request.agent
    if agent_name not in agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent '{agent_name}'. Available: {list(agents.keys())}",
        )

    agent = agents[agent_name]
    start = time.time()

    try:
        output = await agent.run(
            request.message, max_retries_per_step=3, max_iterations=8
        )
        duration = time.time() - start

        agent_requests_total.labels(agent_name=agent_name, status="success").inc()
        agent_request_duration_seconds.labels(agent_name=agent_name).observe(duration)

        return ChatResponse(
            response=output.result.text,
            agent=agent_name,
            duration_seconds=round(duration, 2),
        )
    except Exception as e:
        duration = time.time() - start
        agent_requests_total.labels(agent_name=agent_name, status="error").inc()
        agent_request_duration_seconds.labels(agent_name=agent_name).observe(duration)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT)
