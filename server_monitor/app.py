from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Union

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server_monitor.api import create_router
from server_monitor.collector import MetricsCollector
from server_monitor.config import load_config
from server_monitor.metrics import MonitorStore


def build_app(config_path: Union[str, Path] = "config.yaml") -> FastAPI:
    config = load_config(config_path)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    store = MonitorStore.create(config.buffer_size, config.interfaces)
    collector = MetricsCollector(config, store)

    app = FastAPI(title="Server Monitor", version="1.0.0")
    app.state.config = config
    app.state.store = store
    app.state.collector = collector
    app.include_router(create_router(config, store))

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.on_event("startup")
    async def startup_event() -> None:
        collector.start()

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        collector.stop()

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="In-memory Linux server monitor")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    args = parser.parse_args()

    app = build_app(args.config)
    config = app.state.config
    uvicorn.run(app, host=config.web_host, port=config.web_port)


if __name__ == "__main__":
    main()
