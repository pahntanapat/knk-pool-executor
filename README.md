# Kanokkul's Pool Executor
Kanokkul's AWS Lambda-Compatible process and thread pool executor

## Installation
```sh
pip install knk-pool-executor
```

## Usage
Simply substitute `ProcessPoolExecutor` with `AWSLambdaProcessPoolExecutor` 

```python
from knk_pool_executor import AWSLambdaProcessPoolExecutor

with AWSLambdaProcessPoolExecutor() as pool:
    future = pool.submit(some_function, arg, kw=kw)
    
    # do another thing

    result = future.result()
```

## Inspiration
 - [Parallel Processing in Python with AWS Lambda: AWS Compute Blog](https://aws.amazon.com/th/blogs/compute/parallel-processing-in-python-with-aws-lambda/)
 - [How to emulate multiprocessing.Pool.map() in AWS Lambda?](https://stackoverflow.com/questions/56329799/how-to-emulate-multiprocessing-pool-map-in-aws-lambda)