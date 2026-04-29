from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VLLM_BASE_URL: str = (
        "http://vllm-inference-service-predictor.ai-agent.svc.cluster.local:8080/v1"
    )
    MODEL_NAME: str = "granite-4.0-h-small"
    OPENAI_API_KEY: str = "EMPTY"
    SAMPLE_API_URL: str = "http://sample-api.ai-agent.svc.cluster.local:8080"
    AGENT_MODE: str = "both"
    ENABLED_AGENTS: str = ""
    CUSTOM_AGENTS_DIR: str = ""
    SERVER_PORT: int = 9999
    METRICS_PORT: int = 8000


settings = Settings()
