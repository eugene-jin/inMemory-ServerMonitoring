from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml


@dataclass
class AppConfig:
    collect_interval_seconds: int = 10
    history_window_hours: int = 24
    interfaces: List[str] = field(default_factory=lambda: ["eth0", "eth0.3", "ppp0"])
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    route_test_target: str = "8.8.8.8"
    ru_update_file: str = "/var/lib/ru-nft-last-update"
    vpn_service_name: str = "sstp-vpn.service"
    log_level: str = "INFO"

    @property
    def history_window_seconds(self) -> int:
        return self.history_window_hours * 3600

    @property
    def buffer_size(self) -> int:
        base = max(1, self.collect_interval_seconds)
        return max(10, int(self.history_window_seconds / base) + 2)


def load_config(config_path: Union[str, Path]) -> AppConfig:
    path = Path(config_path)
    data: Dict[str, Any] = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AppConfig(**data)
