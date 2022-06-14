from time import perf_counter
from typing import Optional


class CacheProcessTime:
    start: Optional[float] = None
    stop: Optional[float] = None
    duration: Optional[float] = None

    def __enter__(self):
        self.stop = None
        self.duration = None
        self.start = perf_counter()

    def __exit__(self):
        self.stop = perf_counter()
        self.duration = self.stop - self.start
