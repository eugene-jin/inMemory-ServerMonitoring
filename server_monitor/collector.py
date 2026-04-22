from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

from server_monitor.config import AppConfig
from server_monitor.metrics import MonitorStore

LOGGER = logging.getLogger(__name__)


def _run_command(args: List[str]) -> Optional[str]:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
        LOGGER.debug("Command failed %s: %s", args, exc)
        return None
    if completed.returncode != 0:
        LOGGER.debug("Command returned %s for %s: %s", completed.returncode, args, completed.stderr.strip())
        return None
    return completed.stdout.strip()


def _read_temperature() -> Optional[float]:
    sensors = psutil.sensors_temperatures(fahrenheit=False)
    for entries in sensors.values():
        for entry in entries:
            if entry.current is not None:
                return float(entry.current)

    output = _run_command(["vcgencmd", "measure_temp"])
    if output and "=" in output:
        raw = output.split("=", 1)[1].replace("'C", "").strip()
        try:
            return float(raw)
        except ValueError:
            LOGGER.debug("Unexpected vcgencmd output: %s", output)

    thermal_zone = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal_zone.exists():
        try:
            value = thermal_zone.read_text(encoding="utf-8").strip()
            return float(value) / 1000.0
        except (OSError, ValueError) as exc:
            LOGGER.debug("Failed reading thermal zone: %s", exc)
    return None


def _get_interface_state(interface: str) -> Tuple[Optional[bool], Optional[str]]:
    stats = psutil.net_if_stats().get(interface)
    addresses = psutil.net_if_addrs().get(interface, [])
    ip_address = None
    for addr in addresses:
        if getattr(addr.family, "name", "") == "AF_INET":
            ip_address = addr.address
            break
    return (stats.isup if stats else None, ip_address)


def _service_is_active(service_name: str) -> Optional[bool]:
    output = _run_command(["systemctl", "is-active", service_name])
    if output is None:
        return None
    return output.strip() == "active"


def _route_via_interface(target: str, interface: str) -> Optional[bool]:
    output = _run_command(["ip", "route", "get", target])
    if output is None:
        return None
    return f" dev {interface} " in f" {output} "


def _route_table_exists(table_name: str) -> Optional[bool]:
    output = _run_command(["ip", "route", "show", "table", table_name])
    if output is None:
        return None
    return bool(output.strip())


def _ru_update_timestamp(path: str) -> Optional[float]:
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        stat = file_path.stat()
    except OSError as exc:
        LOGGER.warning("Failed to stat RU update file %s: %s", path, exc)
        return None
    return stat.st_mtime


class MetricsCollector:
    def __init__(self, config: AppConfig, store: MonitorStore) -> None:
        self.config = config
        self.store = store
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_net_counters: Dict[str, Tuple[float, float, float]] = {}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="metrics-collector", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            started = time.time()
            try:
                self.collect_once(started)
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Unexpected metrics collection error: %s", exc)
            elapsed = time.time() - started
            sleep_for = max(0.0, self.config.collect_interval_seconds - elapsed)
            self._stop_event.wait(timeout=sleep_for)

    def collect_once(self, now: Optional[float] = None) -> None:
        timestamp = now or time.time()
        self.store.cpu.append(timestamp, float(psutil.cpu_percent(interval=None)))
        self.store.ram.append(timestamp, float(psutil.virtual_memory().percent))
        self.store.load1.append(timestamp, float(os.getloadavg()[0]))

        temperature = _read_temperature()
        if temperature is not None:
            self.store.temperature.append(timestamp, temperature)

        self._collect_network(timestamp)
        self._collect_infra()

    def _collect_network(self, timestamp: float) -> None:
        counters = psutil.net_io_counters(pernic=True)
        for interface in self.config.interfaces:
            state, ip_address = _get_interface_state(interface)
            current = counters.get(interface)
            rx_rate = None
            tx_rate = None

            if current is not None:
                previous = self._last_net_counters.get(interface)
                if previous is not None:
                    prev_ts, prev_recv, prev_sent = previous
                    delta_t = max(timestamp - prev_ts, 1e-6)
                    rx_rate = max(0.0, (current.bytes_recv - prev_recv) / delta_t)
                    tx_rate = max(0.0, (current.bytes_sent - prev_sent) / delta_t)
                    self.store.network[interface]["rx"].append(timestamp, rx_rate)
                    self.store.network[interface]["tx"].append(timestamp, tx_rate)
                    self.store.peak_stats[interface].update(timestamp, rx_rate, tx_rate)
                self._last_net_counters[interface] = (timestamp, current.bytes_recv, current.bytes_sent)

            status = self.store.status[interface]
            status.is_up = state
            status.ip_address = ip_address
            status.rx_rate = rx_rate
            status.tx_rate = tx_rate

    def _collect_infra(self) -> None:
        self.store.infra.vpn_service_active = _service_is_active(self.config.vpn_service_name)
        self.store.infra.default_route_via_vpn = _route_via_interface(self.config.route_test_target, "ppp0")
        self.store.infra.table_direct_exists = _route_table_exists("direct")
        self.store.infra.ru_update_timestamp = _ru_update_timestamp(self.config.ru_update_file)
