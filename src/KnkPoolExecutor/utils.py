from time import perf_counter
from traceback import print_exception


class CacheProcessTime:
    start: float = None
    stop: float = None
    duration: float = None

    def __enter__(self):
        self.stop = None
        self.duration = None
        self.start = perf_counter()

    def __exit__(self, exc_type, exc_value, tb):
        self.stop = perf_counter()
        self.duration = self.stop - self.start
        if exc_type is not None:
            print_exception(exc_type, exc_value, tb)
