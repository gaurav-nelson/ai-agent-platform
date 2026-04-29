import os

import gradio as gr
import httpx
from prometheus_client import Counter, start_http_server

AGENT_SERVICE_URL = os.environ.get("AGENT_SERVICE_URL", "http://bee-agent-service:9999")
METRICS_PORT = int(os.environ.get("METRICS_PORT", "8000"))

ui_requests = Counter(
    "agent_ui_requests_total", "Total chat requests from UI", ["agent"]
)


def get_available_agents():
    try:
        resp = httpx.get(f"{AGENT_SERVICE_URL}/agents", timeout=5)
        return resp.json().get("agents", ["cluster-health"])
    except Exception:
        return ["cluster-health", "api-explorer"]


def chat(message, history, agent_name):
    ui_requests.labels(agent=agent_name).inc()
    try:
        resp = httpx.post(
            f"{AGENT_SERVICE_URL}/chat",
            json={"message": message, "agent": agent_name},
            timeout=300,
        )
        if resp.status_code == 200:
            data = resp.json()
            response_text = data["response"]
            duration = data.get("duration_seconds", "?")
            return (
                f"{response_text}\n\n---\n*Agent: {agent_name} | Duration: {duration}s*"
            )
        else:
            return f"Error: {resp.status_code} - {resp.text}"
    except httpx.TimeoutException:
        return "Error: Request timed out. The agent may still be processing."
    except Exception as e:
        return f"Error: {e}"


agents = get_available_agents()

with gr.Blocks(title="AI Agent Platform", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Agent Platform")
    gr.Markdown(
        "Interact with AI agents powered by the Bee AI Framework and IBM Granite. "
        "Select an agent and ask questions about your cluster or explore APIs."
    )

    with gr.Row():
        agent_dropdown = gr.Dropdown(
            choices=agents,
            value=agents[0] if agents else "cluster-health",
            label="Select Agent",
            interactive=True,
        )

    chatbot = gr.ChatInterface(
        fn=chat,
        additional_inputs=[agent_dropdown],
        examples=[
            ["What is the health of my cluster?"],
            ["List all pods in the ai-agent namespace"],
            ["Are there any warning events in the default namespace?"],
            ["List all items in the inventory"],
            ["Create a new item called Widget D with quantity 75 and price 12.99"],
        ],
    )

if __name__ == "__main__":
    start_http_server(METRICS_PORT)
    demo.launch(server_name="0.0.0.0", server_port=7860)
