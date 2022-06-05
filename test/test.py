from math import log
import numpy as np
from os import cpu_count
from time import sleep, perf_counter

# Simulate parallel processing with sleep >> Capture time and compare
sleep(1)
# Series sleep
for loop in range(cpu_count()):
    sleep(1)


for loop in range(4*cpu_count()):
    sleep(1)
# StackTracedThreadPoolExecutor sleep
# StackTracedProcessPoolExecutor sleep
# PipeProcessPoolExecutor sleep

# Simulate parallel processing with GIL-released process
np.log(np.arange(100000))

for loop in range(cpu_count()):
    np.log(np.arange(100000))

# Simulate parallel processing with GIL process
for i in range(100000):
    log(i)

# Series
for loop in range(cpu_count()):
    for i in range(100000):
        log(i)
