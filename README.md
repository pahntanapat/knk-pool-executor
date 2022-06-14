# Kanokkul's Pool Executor
Kanokkul's Pool Executor contains `ProcessPoolExecutor` and `ThreadPoolExecutor` which preserve traceback output for exception. This package also has `StackTracedProcessPoolExecutor` for environment without `/dev/shm`
## Installation
```sh
pip install KnKPoolExecutor
```

## Usage
Simply substitute `ProcessPoolExecutor` with `PipeProcessPoolExecutor` or `StackTracedProcessPoolExecutor`  
Replace `ThreadPoolExecutor` with `StackTracedThreadPoolExecutor`

```python
from knk_pool_executor import PipeProcessPoolExecutor

with PipeProcessPoolExecutor() as pool:
    future = pool.submit(some_function, arg, kw=kw)
    
    # do another thing

    result = future.result()
```

## Inspiration
 - [Parallel Processing in Python with AWS Lambda: AWS Compute Blog](https://aws.amazon.com/th/blogs/compute/parallel-processing-in-python-with-aws-lambda/)
 - [How to emulate multiprocessing.Pool.map() in AWS Lambda?](https://stackoverflow.com/questions/56329799/how-to-emulate-multiprocessing-pool-map-in-aws-lambda)
 - [se7entyse7en](https://stackoverflow.com/users/3276106/se7entyse7en)'s [answer in StackOverflow about Getting original line number for exception in concurrent.futures](https://stackoverflow.com/a/24457608)
