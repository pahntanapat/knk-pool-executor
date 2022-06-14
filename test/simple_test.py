
from concurrent.futures import ALL_COMPLETED, wait
from time import sleep
import sys
import os
from unittest import TestCase

## Add src dir to import path for debugging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from KnkPoolExecutor import PipeProcessPoolExecutor

class TestResult(TestCase):
    pass


if __name__ == '__main__':
    with PipeProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        for i in r:
            print(i.result())
