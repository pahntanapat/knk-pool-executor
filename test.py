from concurrent.futures import ALL_COMPLETED, wait
from time import sleep, perf_counter
import time
from math import log
import numpy as np
from os import cpu_count

from src.KnkPoolExecutor import PipeProcessPoolExecutor, StackTracedThreadPoolExecutor, StackTracedProcessPoolExecutor

if __name__ == '__main__':
    with StackTracedThreadPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        t1str = perf_counter()
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In StackTracedThreadPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        wnp = [pool.submit(np.log, i) for i in range(1, 10)]
        wait(wnp, return_when=ALL_COMPLETED)
        t2str = perf_counter()
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In StackTracedThreadPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        gil = [pool.submit(log, i) for i in range(1, 10)]
        wait(gil, return_when=ALL_COMPLETED)
        t3str = perf_counter()
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In StackTracedThreadPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))

    with StackTracedProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        t1str = perf_counter()
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In StackTracedProcessPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        wnp = [pool.submit(np.log, i) for i in range(1, 10)]
        wait(wnp, return_when=ALL_COMPLETED)
        t2str = perf_counter()
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In StackTracedProcessPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        gil = [pool.submit(log, i) for i in range(1, 10)]
        wait(gil, return_when=ALL_COMPLETED)
        t3str = perf_counter()
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In StackTracedProcessPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))

    with PipeProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        t1str = perf_counter()
        for i in r:
            print(i.result())
        t1stp = perf_counter()
        print("In PipeProcessPoolExecutor sleep : --- %s seconds ---" %
              (t1stp - t1str))

        wnp = [pool.submit(np.log, i) for i in range(1, 10)]
        wait(wnp, return_when=ALL_COMPLETED)
        t2str = perf_counter()
        for i in wnp:
            print(i.result())
        t2stp = perf_counter()
        print("In PipeProcessPoolExecutor np : --- %s seconds ---" %
              (t2stp - t2str))

        gil = [pool.submit(log, i) for i in range(1, 10)]
        wait(gil, return_when=ALL_COMPLETED)
        t3str = perf_counter()
        for i in gil:
            print(i.result())
        t3stp = perf_counter()
        print("In PipeProcessPoolExecutor gil : --- %s seconds ---" %
              (t3stp - t3str))
