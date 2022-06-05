from concurrent.futures import ALL_COMPLETED, wait
from time import sleep
from src.KnkPoolExecutor import PipeProcessPoolExecutor

if __name__=='__main__':
    with PipeProcessPoolExecutor() as pool:
        r = [pool.submit(sleep, 1) for _ in range(10)]
        wait(r, return_when=ALL_COMPLETED)
        for i in r:
            print(i.result())