__author__ = 'Tanapat Kahabodeekanokkul (pahntanapat@gmail.com)'
from .base import AWSLambdaProcessPoolExecutor, AWSPoolFuture


def __getattr__(name):
    global AWSLambdaProcessPoolExecutor, AWSPoolFuture

    if name == 'AWSLambdaProcessPoolExecutor':
        from .base import AWSLambdaProcessPoolExecutor as pe
        AWSLambdaProcessPoolExecutor = pe
        return pe

    if name == 'AWSPoolFuture':
        from .base import AWSPoolFuture as f
        AWSPoolFuture = f
        return f

    raise AttributeError(f"module {__name__} has no attribute {name}")
