"""
FastAPI application for the LegacyDataEnv Environment.

Bug Fix #7: Replace hand-rolled FastAPI with the official create_app() factory.
This sets up the correct /reset, /step, /state, /schema, /health, and /ws
endpoints that the OpenEnv validator expects, with proper serialization.

Endpoints (managed by create_app):
    - POST /reset  : Reset the environment
    - POST /step   : Execute an action
    - GET  /state  : Get current environment state
    - GET  /schema : Get action/observation/state JSON schemas
    - GET  /health : Health check
    - WS   /ws     : WebSocket endpoint for persistent sessions

Usage:
    uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
"""

from openenv.core.env_server import create_app

try:
    from ..models import LegacyAction, LegacyObservation
    from ..env import LegacyDataEnvironment
except ImportError:
    from envs.legacy_data.models import LegacyAction, LegacyObservation
    from envs.legacy_data.env import LegacyDataEnvironment


# Create the fully-compliant OpenEnv FastAPI application
app = create_app(
    LegacyDataEnvironment,
    LegacyAction,
    LegacyObservation,
    env_name="legacy-data-env",
    max_concurrent_envs=4,
)


def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for the openenv-server CLI script defined in pyproject.toml."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LegacyDataEnv Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    main(host=args.host, port=args.port)