from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from server_monitor.buffer import MetricBuffer


NUMERIC_METRICS = {
    "cpu": "avg",
    "ram": "avg",
    "load1": "avg",
    "temperature": "avg",
    "net_rx": "avg",
    "net_tx": "avg",
}


@dataclass
class NetworkStatus:
    is_up: Optional[bool] = None
    ip_address: Optional[str] = None
    rx_rate: Optional[float] = None
    tx_rate: Optional[float] = None


@dataclass
class NetworkPeakStats:
    max_rx: float = 0.0
    max_tx: float = 0.0
    max_rx_timestamp: Optional[float] = None
    max_tx_timestamp: Optional[float] = None

    def update(self, timestamp: float, rx_rate: Optional[float], tx_rate: Optional[float]) -> None:
        if rx_rate is not None and rx_rate > self.max_rx:
            self.max_rx = rx_rate
            self.max_rx_timestamp = timestamp
        if tx_rate is not None and tx_rate > self.max_tx:
            self.max_tx = tx_rate
            self.max_tx_timestamp = timestamp

    def reset(self) -> None:
        self.max_rx = 0.0
        self.max_tx = 0.0
        self.max_rx_timestamp = None
        self.max_tx_timestamp = None


@dataclass
class InfrastructureStatus:
    vpn_service_active: Optional[bool] = None
    default_route_via_vpn: Optional[bool] = None
    table_direct_exists: Optional[bool] = None
    ru_update_timestamp: Optional[float] = None


@dataclass
class MonitorStore:
    cpu: MetricBuffer
    ram: MetricBuffer
    load1: MetricBuffer
    temperature: MetricBuffer
    network: Dict[str, Dict[str, MetricBuffer]]
    status: Dict[str, NetworkStatus] = field(default_factory=dict)
    peak_stats: Dict[str, NetworkPeakStats] = field(default_factory=dict)
    infra: InfrastructureStatus = field(default_factory=InfrastructureStatus)

    @classmethod
    def create(cls, buffer_size: int, interfaces: List[str]) -> "MonitorStore":
        return cls(
            cpu=MetricBuffer(buffer_size),
            ram=MetricBuffer(buffer_size),
            load1=MetricBuffer(buffer_size),
            temperature=MetricBuffer(buffer_size),
            network={
                interface: {
                    "rx": MetricBuffer(buffer_size),
                    "tx": MetricBuffer(buffer_size),
                }
                for interface in interfaces
            },
            status={interface: NetworkStatus() for interface in interfaces},
            peak_stats={interface: NetworkPeakStats() for interface in interfaces},
        )
