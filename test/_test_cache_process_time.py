from statistics import mean, stdev
from typing import Iterable, Type, Union

from time import sleep, perf_counter
from unittest import TestCase, TestSuite, TextTestRunner

try:
    from KnkPoolExecutor.utils import CacheProcessTime
except:
    import sys
    import os
    # Add src dir to import path for debugging
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from KnkPoolExecutor.utils import CacheProcessTime


def t_ind(samp1: Iterable[float], samp2: Iterable[float]):
    m1, m2 = mean(samp1), mean(samp2)
    s1, s2 = stdev(samp1), stdev(samp2)
    print(m1, '+-', s1, ';', m2, '+-', s2)
    

# class TestCacheProcessTime(TestCase):


def test_pass(self):
    t_norm = []
    for _ in range(1000):
        t1 = perf_counter()
        pass
        t2 = perf_counter()
        t_norm.append(t2-t1)

    t_class = []
    for _ in range(1000):
        with CacheProcessTime() as t:
            pass
        t_class.append(t.duration)

    print(mean)
