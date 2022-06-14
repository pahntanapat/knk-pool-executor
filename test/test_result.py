
from multiprocessing import cpu_count, freeze_support
from typing import Type, Union
from KnkPoolExecutor import PipeProcessPoolExecutor
from concurrent.futures import ALL_COMPLETED, Executor, ProcessPoolExecutor, ThreadPoolExecutor, wait
from time import sleep
import sys
import os
from unittest import TestCase

# Add src dir to import path for debugging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPoolResult(TestCase):
    def __init__(self, pool: Union[Type[ThreadPoolExecutor], Type[ProcessPoolExecutor]], pool_size: int = cpu_count(), methodName: str = None) -> None:
        freeze_support()
        self.pool = None
        self.pool_class = pool
        self.pool_size = pool_size
        if methodName is None:
            super().__init__('{}:{}({})'.format(
                self.__class__.__name__, self.pool.__class__.__name__, pool_size))
        else:
            super().__init__(methodName)

    def setUp(self) -> None:
        self.pool = self.pool_class(self.pool_size)
        return super().setUp()

    def tearDown(self) -> None:
        if self.pool is not None:
            self.pool.shutdown(wait=False)
            self.pool = None
        return super().tearDown()

    def test_map_sleep(self):
        for k, v in enumerate(self.pool.map(sleep, [1]*self.pool_size)):
            self.assertIsNone(
                v, 'pool.map(sleep, [1]*pool_size) at index: '+str(k))

    def test_map_sleep(self):
        for k, v in enumerate(self.pool.map(sleep, [1]*self.pool_size)):
            self.assertIsNone(
                v, 'pool.map(sleep, [1]*pool_size) at index: '+str(k))

if __name__ == '__main__':
    with PipeProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        for i in r:
            print(i.result())
