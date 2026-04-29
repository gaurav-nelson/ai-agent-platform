import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BUILTIN_AGENTS_DIR = Path(__file__).parent / "agents"


def discover_agents(
    enabled: str,
    custom_dir: str,
    llm: Any,
    legacy_mode: str = "",
) -> dict:
    if not enabled:
        return _legacy_load(legacy_mode, llm)

    available = {}
    available.update(_scan_directory(BUILTIN_AGENTS_DIR, package="app.agents"))
    if custom_dir:
        available.update(_scan_directory(Path(custom_dir)))

    if enabled == "all":
        names_to_load = list(available.keys())
    else:
        names_to_load = [n.strip() for n in enabled.split(",") if n.strip()]

    agents = {}
    for name in names_to_load:
        if name not in available:
            logger.warning(f"Agent '{name}' requested but not found")
            continue
        try:
            mod = available[name]
            agents[name] = mod.create_agent(llm)
            logger.info(f"Registered agent: {name}")
        except Exception as e:
            logger.warning(f"Failed to initialize agent '{name}': {e}")

    return agents


def _scan_directory(directory: Path, package: str | None = None) -> dict:
    found = {}
    if not directory.is_dir():
        return found

    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            if package:
                mod = importlib.import_module(f"{package}.{path.stem}")
            else:
                spec = importlib.util.spec_from_file_location(path.stem, path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[path.stem] = mod
                spec.loader.exec_module(mod)

            agent_name = getattr(mod, "AGENT_NAME", None)
            create_fn = getattr(mod, "create_agent", None)
            if agent_name and callable(create_fn):
                found[agent_name] = mod
            else:
                logger.debug(
                    f"Skipping {path.name}: missing AGENT_NAME or create_agent"
                )
        except Exception as e:
            logger.warning(f"Error loading agent module {path.name}: {e}")

    return found


def _legacy_load(mode: str, llm: Any) -> dict:
    agents = {}
    if mode in ("cluster-health", "both"):
        try:
            from app.agents.cluster_health import create_cluster_health_agent
            agents["cluster-health"] = create_cluster_health_agent(llm)
            logger.info("Registered cluster-health agent (legacy mode)")
        except Exception as e:
            logger.warning(f"Failed to initialize cluster-health agent: {e}")

    if mode in ("api-explorer", "both"):
        try:
            from app.agents.api_explorer import create_api_explorer_agent
            agents["api-explorer"] = create_api_explorer_agent(llm)
            logger.info("Registered api-explorer agent (legacy mode)")
        except Exception as e:
            logger.warning(f"Failed to initialize api-explorer agent: {e}")

    return agents
