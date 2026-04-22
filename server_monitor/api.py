from __future__ import annotations

import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from server_monitor.config import AppConfig
from server_monitor.metrics import NUMERIC_METRICS, MonitorStore

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


PERIOD_MAP = {
    "1h": 3600,
    "24h": 24 * 3600,
    "7d": 7 * 24 * 3600,
}

STEP_MAP = {
    "raw": 0,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30s": 30,
}

ESTIMATED_SAMPLE_BYTES = 160


def create_router(config: AppConfig, store: MonitorStore) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"interfaces": config.interfaces},
        )

    @router.get("/api/status")
    async def status() -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": _latest_value(store.cpu),
            "ram": _latest_value(store.ram),
            "load1": _latest_value(store.load1),
            "temperature": _latest_value(store.temperature),
            "interfaces": {
                name: {
                    "is_up": state.is_up,
                    "ip_address": state.ip_address,
                    "rx_rate": state.rx_rate,
                    "tx_rate": state.tx_rate,
                }
                for name, state in store.status.items()
            },
            "vpn_service_active": store.infra.vpn_service_active,
            "default_route_via_vpn": store.infra.default_route_via_vpn,
            "table_direct_exists": store.infra.table_direct_exists,
            "ru_update_timestamp": _iso_timestamp(store.infra.ru_update_timestamp),
            "history_memory": _history_memory(config, store),
            "disk_usage": _disk_usage("/"),
        }

    @router.get("/api/metrics")
    async def metrics() -> Dict[str, Any]:
        return {
            "metrics": [
                {"name": "cpu", "type": "numeric"},
                {"name": "ram", "type": "numeric"},
                {"name": "load1", "type": "numeric"},
                {"name": "temperature", "type": "numeric"},
                {"name": "net", "type": "network", "interfaces": config.interfaces},
            ]
        }

    @router.get("/api/peak-stats")
    async def peak_stats() -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interfaces": {
                name: {
                    "max_rx": stats.max_rx,
                    "max_tx": stats.max_tx,
                    "max_rx_timestamp": _iso_timestamp(stats.max_rx_timestamp),
                    "max_tx_timestamp": _iso_timestamp(stats.max_tx_timestamp),
                }
                for name, stats in store.peak_stats.items()
            },
        }

    @router.post("/api/peak-stats/reset")
    async def reset_peak_stats() -> Dict[str, Any]:
        for stats in store.peak_stats.values():
            stats.reset()
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/api/history")
    async def history(
        metric: str,
        period: str = "1h",
        step: str = "raw",
        interface: Optional[str] = None,
    ) -> Dict[str, Any]:
        if period not in PERIOD_MAP:
            raise HTTPException(status_code=400, detail="Unsupported period")
        if step not in STEP_MAP:
            raise HTTPException(status_code=400, detail="Unsupported step")

        start_ts = time.time() - PERIOD_MAP[period]
        step_seconds = STEP_MAP[step]

        if metric == "net":
            if not interface or interface not in store.network:
                raise HTTPException(status_code=400, detail="Network interface is required")
            reducer = "avg"
            rx_points = store.network[interface]["rx"].aggregate(start_ts, step_seconds, reducer=reducer)
            tx_points = store.network[interface]["tx"].aggregate(start_ts, step_seconds, reducer=reducer)
            return {
                "metric": metric,
                "interface": interface,
                "period": period,
                "step": step,
                "series": {
                    "rx": _format_points(rx_points),
                    "tx": _format_points(tx_points),
                },
            }

        if metric not in NUMERIC_METRICS:
            raise HTTPException(status_code=400, detail="Unsupported metric")

        buffer = getattr(store, metric)
        points = buffer.aggregate(start_ts, step_seconds, reducer=NUMERIC_METRICS[metric])
        return {
            "metric": metric,
            "period": period,
            "step": step,
            "points": _format_points(points),
        }

    return router


def _format_points(points: List[Dict[str, float]]) -> List[Dict[str, Union[float, str]]]:
    return [
        {
            "timestamp": datetime.fromtimestamp(point["timestamp"], tz=timezone.utc).isoformat(),
            "value": point["value"],
        }
        for point in points
    ]


def _latest_value(buffer) -> Optional[float]:
    sample = buffer.latest()
    return sample.value if sample else None


def _iso_timestamp(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _history_memory(config: AppConfig, store: MonitorStore) -> Dict[str, int]:
    buffers = [
        store.cpu,
        store.ram,
        store.load1,
        store.temperature,
    ]
    for series in store.network.values():
        buffers.append(series["rx"])
        buffers.append(series["tx"])

    used_points = sum(len(buffer) for buffer in buffers)
    capacity_points = config.buffer_size * len(buffers)
    return {
        "buffers": len(buffers),
        "points_per_buffer": config.buffer_size,
        "used_points": used_points,
        "capacity_points": capacity_points,
        "estimated_used_bytes": used_points * ESTIMATED_SAMPLE_BYTES,
        "estimated_capacity_bytes": capacity_points * ESTIMATED_SAMPLE_BYTES,
        "estimated_sample_bytes": ESTIMATED_SAMPLE_BYTES,
    }


def _disk_usage(path: str) -> Dict[str, int]:
    usage = shutil.disk_usage(path)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }
