from concurrent.futures import ALL_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from multiprocessing import cpu_count, freeze_support
from time import sleep, perf_counter
import time
from math import log
from typing import Dict, Type, Union
import numpy as np

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


class CalibrateTime:
    t_sleep: float = 1
    t_np: float = 0
    t_gil: float = 0
    LOOP = 10000000000

    def __init__(self, loop: int = 10000000000) -> None:
        self.LOOP = loop
        t1 = perf_counter()
        sleep(1)
        t2 = perf_counter()
        self.t_sleep = t2-t1

        t1 = perf_counter()
        self.np()
        t2 = perf_counter()
        self.t_np = t2-t1

        t1 = perf_counter()
        self.gil()
        t2 = perf_counter()
        self.t_gil = t2-t1

    @classmethod
    def np(cls, *a):
        np.sum(np.log(1+np.arange(cls.LOOP)))

    @classmethod
    def gil(cls, *a):
        sum(log(i+1) for i in range(cls.LOOP))


class TestPoolTime(TestCase):
    def __init__(self, methodName: str, pool: Union[Type[ThreadPoolExecutor], Type[ProcessPoolExecutor]], pool_worker: int = cpu_count(), test_loop: int = cpu_count(), calibrate_time: CalibrateTime = None, overhead_time: float = 1) -> None:
        freeze_support()
        self.pool = None
        self.pool_class = pool
        self.worker = pool_worker

        self.test_loop = test_loop
        self.test_round = round(test_loop/pool_worker)
        self.calibrate_time = CalibrateTime() if calibrate_time is None else calibrate_time
        self.overhead = overhead_time
        super().__init__(methodName)

    def setUp(self) -> None:
        self.pool = self.pool_class(self.worker)
        return super().setUp()

    def tearDown(self) -> None:
        if self.pool is not None:
            self.pool.shutdown(wait=True)
            self.pool = None
        return super().tearDown()

    def print_result(self, t: float, calibrate: float, func: str = None) -> float:
        if func is None:
            func = self._testMethodName
        print('*'*20)
        print('Func:', func, 'Pool:', self.pool_class.__name__, 'Worker:',
              self.worker, 'TestLoop:', self.test_loop, 'WorkerRound:', self.test_round, 'Overhead:', self.overhead)
        print('Calibrate time:', calibrate,
              'Calibrate * Round:', calibrate * self.test_round)
        print('Used time:', t)
        print('Per worker:', t/self.worker, 'Per worker - set overhead:',
              (t-self.overhead)/self.worker, 'Est. overhead:', t-(calibrate*self.worker))
        print('Per worker round:', t/self.test_round, 'Per worker round - set overhead:',
              (t-self.overhead)/self.test_round, 'Est. overhead:', t-(calibrate*self.test_round))
        print('Per jobs:', t/self.test_loop, 'Per jobs - set overhead:',
              (t-self.overhead)/self.test_loop, 'Est. overhead:', t-(calibrate*self.test_loop))

        self.assertGreaterEqual(
            t, calibrate, 'Jobs duration is shorter than duration of single jobs in main thread.')
        t = (t-self.overhead)/calibrate
        self.assertLessEqual(
            t, self.test_loop, 'Jobs duration is longer than running in main thread.')
        return t

    def test_sleep(self):
        arg = [1] * self.test_loop
        t1 = perf_counter()
        list(self.pool.map(sleep, arg))
        t2 = perf_counter()

        self.assertGreaterEqual(t2-t1, 1, 'Sleep is shorter than 1.')

        self.assertLessEqual(
            self.print_result(t2-t1, self.calibrate_time.t_sleep), self.test_round, 'Jobs (sleep) not done in parallel ({}).'.format(self.pool_class.__name__))

    def test_np(self):
        arg = [None] * self.test_loop
        t1 = perf_counter()
        list(self.pool.map(CalibrateTime.np, arg))
        t2 = perf_counter()

        self.assertLessEqual(
            self.print_result(t2-t1, self.calibrate_time.t_sleep), self.test_round, 'Jobs (NumPy) not done in parallel ({}).'.format(self.pool_class.__name__))

    def test_gil(self):
        arg = [None] * self.test_loop
        t1 = perf_counter()
        list(self.pool.map(sleep, arg))
        t2 = perf_counter()

        if not isinstance(self.pool, ThreadPoolExecutor):
            self.assertLessEqual(
                self.print_result(t2-t1, self.calibrate_time.t_sleep), self.test_round, 'Jobs (GIL math) not done in parallel ({}).'.format(self.pool_class.__name__))


if __name__ == '__main__':
    freeze_support()

    print('Baseline')
    calibrate = CalibrateTime()
    print('sleep: 1', 'used time:', calibrate.t_sleep,
          'np:', calibrate.t_np, 'GIL:', calibrate.gil)

    cpu = cpu_count()
    suite = TestSuite()
    for p in [ProcessPoolExecutor, ThreadPoolExecutor, StackTracedProcessPoolExecutor, StackTracedThreadPoolExecutor, PipeProcessPoolExecutor]:
        for t in ['test_sleep', 'test_np', 'test_gil']:
            for m, a in [[0, 1], [0, cpu//2], [1, 0], [1, 1], [1, cpu//2], [2, 0]]:
                suite.addTest(
                    TestPoolTime(methodName=t, pool=p, test_loop=(
                        cpu*m)+a, calibrate_time=calibrate))

    TextTestRunner().run(suite)
    '''with StackTracedThreadPoolExecutor() as pool:
        t1str = perf_counter()
        r = [pool.submit(sleep, 1) for _ in range(LOOP)]
        wait(r, return_when=ALL_COMPLETED)
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In StackTracedThreadPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        t2str = perf_counter()
        wnp = [pool.submit(np.log, i) for i in range(1, 1+LOOP)]
        wait(wnp, return_when=ALL_COMPLETED)
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In StackTracedThreadPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        t3str = perf_counter()
        gil = [pool.submit(log, i) for i in range(1, 1+LOOP)]
        wait(gil, return_when=ALL_COMPLETED)
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In StackTracedThreadPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))

    with StackTracedProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(LOOP)]
        wait(r, return_when=ALL_COMPLETED)
        t1str = perf_counter()
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In StackTracedProcessPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        wnp = [pool.submit(np.log, i) for i in range(1, 1+LOOP)]
        wait(wnp, return_when=ALL_COMPLETED)
        t2str = perf_counter()
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In StackTracedProcessPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        gil = [pool.submit(log, i) for i in range(1, 1+LOOP)]
        wait(gil, return_when=ALL_COMPLETED)
        t3str = perf_counter()
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In StackTracedProcessPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))

    with PipeProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(LOOP)]
        wait(r, return_when=ALL_COMPLETED)
        t1str = perf_counter()
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In PipeProcessPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        wnp = [pool.submit(np.log, i) for i in range(1, 1+LOOP)]
        wait(wnp, return_when=ALL_COMPLETED)
        t2str = perf_counter()
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In PipeProcessPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        gil = [pool.submit(log, i) for i in range(1, 1+LOOP)]
        wait(gil, return_when=ALL_COMPLETED)
        t3str = perf_counter()
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In PipeProcessPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))'''
