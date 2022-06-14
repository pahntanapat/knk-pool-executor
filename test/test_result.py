from multiprocessing import cpu_count, freeze_support
from typing import Type, Union

from concurrent.futures import ALL_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from time import sleep
from unittest import TestCase, TestSuite, TextTestRunner

try:
    from KnkPoolExecutor import PipeProcessPoolExecutor, StackTracedProcessPoolExecutor, StackTracedThreadPoolExecutor
except:
    import sys
    import os
    # Add src dir to import path for debugging
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from KnkPoolExecutor import PipeProcessPoolExecutor, StackTracedProcessPoolExecutor, StackTracedThreadPoolExecutor


class TestPoolResult(TestCase):
    def __init__(self, methodName: str, pool: Union[Type[ThreadPoolExecutor], Type[ProcessPoolExecutor]], pool_size: int = cpu_count()) -> None:
        freeze_support()
        self.pool = None
        self.pool_class = pool
        self.pool_size = pool_size
        super().__init__(methodName)

    def setUp(self) -> None:
        self.pool = self.pool_class(self.pool_size)
        return super().setUp()

    def tearDown(self) -> None:
        if self.pool is not None:
            self.pool.shutdown(wait=True)
            self.pool = None
        return super().tearDown()

    def test_map_sleep(self):
        for k, v in enumerate(self.pool.map(sleep, [1]*self.pool_size)):
            self.assertIsNone(
                v, 'pool.map(sleep, [1]*pool_size) at index: '+str(k))

    def test_submit_sleep(self):
        ft = [self.pool.submit(sleep, 1) for _ in range(self.pool_size)]
        wait(ft, return_when=ALL_COMPLETED)
        for k, v in enumerate(ft):
            self.assertIsNone(
                v.exception(), 'self.pool.submit(sleep, 1) raises exception at index: '+str(k))
            if v.exception() is None:
                self.assertIsNone(
                    v.result(), 'pool.map(sleep, [1]*pool_size) at index: '+str(k))


if __name__ == '__main__':
    suite = TestSuite()
    for i in {'test_map_sleep', 'test_submit_sleep'}:
        for p in {ProcessPoolExecutor, ThreadPoolExecutor, StackTracedProcessPoolExecutor, StackTracedThreadPoolExecutor, PipeProcessPoolExecutor}:
            suite.addTest(TestPoolResult(i, p))
    TextTestRunner().run(suite)
