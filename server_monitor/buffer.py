from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean
from threading import Lock
from typing import Deque, Dict, List, Optional


@dataclass
class Sample:
    timestamp: float
    value: float


class MetricBuffer:
    def __init__(self, maxlen: int) -> None:
        self._samples: Deque[Sample] = deque(maxlen=maxlen)
        self._lock = Lock()

    def append(self, timestamp: float, value: float) -> None:
        with self._lock:
            self._samples.append(Sample(timestamp=timestamp, value=value))

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)

    def latest(self) -> Optional[Sample]:
        with self._lock:
            return self._samples[-1] if self._samples else None

    def get_since(self, start_ts: float) -> List[Sample]:
        with self._lock:
            return [sample for sample in self._samples if sample.timestamp >= start_ts]

    def aggregate(self, start_ts: float, step_seconds: int, reducer: str = "avg") -> List[Dict[str, float]]:
        samples = self.get_since(start_ts)
        if not samples:
            return []
        if step_seconds <= 0:
            return [{"timestamp": sample.timestamp, "value": sample.value} for sample in samples]

        buckets: Dict[int, List[float]] = {}
        for sample in samples:
            bucket_ts = int((sample.timestamp - start_ts) // step_seconds) * step_seconds + int(start_ts)
            buckets.setdefault(bucket_ts, []).append(sample.value)

        points: List[Dict[str, float]] = []
        for bucket_ts in sorted(buckets):
            values = buckets[bucket_ts]
            if reducer == "sum":
                value = float(sum(values))
            elif reducer == "max":
                value = float(max(values))
            else:
                value = float(mean(values))
            points.append({"timestamp": float(bucket_ts), "value": value})
        return points
