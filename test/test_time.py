from concurrent.futures import ALL_COMPLETED, wait
from multiprocessing import cpu_count, freeze_support
from time import sleep, perf_counter
import time
from math import log
import numpy as np
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from KnkPoolExecutor import PipeProcessPoolExecutor, StackTracedThreadPoolExecutor, StackTracedProcessPoolExecutor
LOOP = cpu_count()
if __name__ == '__main__':
    freeze_support()

    print('Baseline')



    with StackTracedThreadPoolExecutor() as pool:
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
              (t3stp - t3str))
