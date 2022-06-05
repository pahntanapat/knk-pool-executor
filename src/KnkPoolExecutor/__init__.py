__author__ = 'Tanapat Kahabodeekanokkul (pahntanapat@gmail.com)'

from concurrent.futures import (
    CancelledError,
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    Future,
)
from concurrent.futures._base import (
    FINISHED,
    CANCELLED,
    CANCELLED_AND_NOTIFIED,
)
from concurrent.futures.thread import (
    _WorkItem,
    BrokenThreadPool,
    _shutdown,
)

import gc
from logging import Logger, getLogger
from multiprocessing import Pipe, freeze_support, get_context, cpu_count
from multiprocessing.connection import Connection
import sys
import traceback
from typing import Any, Callable, Iterable, Iterator, Optional, Tuple, TypeVar, Union

gc.enable()

_T = TypeVar("_T")


def function_wrapper(fn, *args, **kwargs):
    """Wraps `fn` in order to preserve the traceback of any kind of
    raised exception

    """
    try:
        return fn(*args, **kwargs)
    except Exception:
        raise sys.exc_info()[0](traceback.format_exc())  # Creates an
        # exception of the
        # same type with the
        # traceback as
        # message


class StackTracedThreadPoolExecutor(ThreadPoolExecutor):
    """

    We acknowledge [se7entyse7en](https://stackoverflow.com/users/3276106/se7entyse7en)'s [answer in StackOverflow](https://stackoverflow.com/a/24457608).
    """

    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super().submit(function_wrapper, fn, *args, **kwargs)

    def map_args(self,
                 fn: Callable[..., _T],
                 iterable: Iterable[Any],
                 *args,
                 timeout: Optional[float] = None,
                 chunksize: Optional[int] = None) -> Iterator[_T]:
        l = len(iterable)
        iterables = [iterable] + [[i] * l for i in args]
        return super().map(fn,
                           *iterables,
                           timeout=timeout,
                           chunksize=chunksize)


class StackTracedProcessPoolExecutor(ProcessPoolExecutor):
    """

    We acknowledge [se7entyse7en](https://stackoverflow.com/users/3276106/se7entyse7en)'s [answer in StackOverflow](https://stackoverflow.com/a/24457608).
    """

    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super().submit(function_wrapper, fn, *args, **kwargs)

    def map_args(self,
                 fn: Callable[..., _T],
                 iterable: Iterable[Any],
                 *args,
                 timeout: Optional[float] = None,
                 chunksize: Optional[int] = None) -> Iterator[_T]:
        l = len(iterable)
        iterables = [iterable] + [[i] * l for i in args]
        if (chunksize is not None) and (chunksize < 0):
            chunksize = max(1, l // (10 * self._max_workers))
        return super().map(fn,
                           *iterables,
                           timeout=timeout,
                           chunksize=chunksize)


class PipePoolFuture(Future):
    def cancel(self):
        """Cancel the future if possible.

        Returns True if the future was cancelled, False otherwise. A future
        cannot be cancelled if it is running or has already completed.
        """
        with self._condition:
            if self._state in {FINISHED}:
                return False

            if self._state in {CANCELLED, CANCELLED_AND_NOTIFIED}:
                return True

            self._state = CANCELLED
            self._condition.notify_all()

        self._invoke_callbacks()
        return True


class _ProcessWorkItem(_WorkItem):
    THREAD_SLEEP = 0.001

    def __init__(
        self,
        future: PipePoolFuture,
        fn: Callable,
        # logger: Logger,
        args,
        kwargs,
        initializer: Optional[Callable] = None,
        initargs: Tuple[Any, ...] = tuple(),
        mp_method: Optional[str] = None,
        thread_sleep: Optional[float] = 0.001
    ):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        #self.logger = logger
        self.mp_method = mp_method
        self.initializer = initializer
        self.initargs = initargs

        if (thread_sleep) and (thread_sleep > 0):
            self.THREAD_SLEEP = thread_sleep

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            main, sub = Pipe()
            proc = get_context(self.mp_method).Process(
                target=self.process_worker,
                args=[self.fn, sub] + list(self.args),
                initializer=self.initializer,
                initargs=self.initargs,
                kwargs=self.kwargs,
            )
            proc.start()

            while proc.is_alive() and not (main.poll(None) or self.future.cancelled()):
                proc.join(self.THREAD_SLEEP)

            if main.poll(0):
                status, result = main.recv()

                if status:
                    self.future.set_result(result)
                else:
                    self.future.set_exception(result)

                main.close()
            elif self.future.cancelled():
                if proc.is_alive():
                    proc.terminate()
                    status = "The {mp} process of {fn} (pid: {pid}) ended by future.cancel() with exitcode: {exitcode}."
                    kws = dict(mp=self.mp_method,
                               fn=self.fn.__name__,
                               pid=proc.pid, exitcode=proc.exitcode())

                    #self.logger.info(status, **kws)
                    raise CancelledError(status.format_map(kws))
                raise CancelledError()
            else:
                raise RuntimeError(
                    "The {mp} process of {fn} (pid: {pid}) ended with code {code} by unknown reason - {fn}(*{arg},**{kw}).".format(
                        mp=self.mp_method,
                        fn=self.fn.__name__,
                        arg=self.args,
                        kw=self.kwargs,
                        pid=proc.pid,
                        code=proc.exitcode(),
                    )
                )

        except:
            # self.logger.exception('Exception from run process: {}', exc)
            self.future.set_exception(
                sys.exc_info()[0](traceback.format_exc()))
            # Break a reference cycle with the exception 'exc'
            self = None

    @staticmethod
    def process_worker(pipe: Connection, fn: Callable, /, *arg, initializer: Optional[Callable] = None, initargs: Tuple[Any, ...] = tuple(), **kw):
        try:
            if initializer is not None:
                initializer(*initargs)
            result = fn(*arg, **kw)
            pipe.send([True, result])
        except:
            pipe.send([False, sys.exc_info()[0](traceback.format_exc())])

        pipe.close()
        return gc.collect()


class PipeProcessPoolExecutor(ThreadPoolExecutor):
    """ProcessPoolExecutor for environment without /dev/shm
    PipeProcessPoolExecutor enable multi-cpu parallel processing in Python as same as ProcessPoolExecutor in environment without /dev/shm (shared memory for processes) support, i.e. AWS Lambda.

    Acknowlegdement
    ---------------
     - [Parallel Processing in Python with AWS Lambda, AWS Compute Blog](https://aws.amazon.com/th/blogs/compute/parallel-processing-in-python-with-aws-lambda/)
     - [AWS Lambda Memory Vs CPU configuration](https://stackoverflow.com/a/66523153)


    """

    def __init__(
        self,
        max_workers: Union[int, None] = None,
        thread_name_prefix: Optional[str] = None,
        initializer: Optional[Callable[..., None]] = None,
        initargs: Optional[Tuple[Any, ...]] = None,
        # logger: Optional[Logger] = None,
        mp_method: Optional[str] = None,
        thread_sleep: Optional[float] = None
    ) -> None:

        if max_workers is None:
            max_workers = 1 + (cpu_count() * 2)

        super().__init__(max_workers, thread_name_prefix, initializer, initargs)
        # self.logger = getLogger() if (logger is None) else logger
        self.mp_method = mp_method
        self.thread_sleep = thread_sleep

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        with self._shutdown_lock:
            if self._broken:
                raise BrokenThreadPool(self._broken)

            if self._shutdown:
                raise RuntimeError(
                    "cannot schedule new futures after shutdown")
            if _shutdown:
                raise RuntimeError(
                    "cannot schedule new futures after interpreter shutdown"
                )

            f = PipePoolFuture()
            w = _ProcessWorkItem(f, fn,
                                 # self.logger,
                                 args, kwargs,
                                 initializer=self._initializer,
                                 initargs=self._initargs,
                                 mp_method=self.mp_method,
                                 thread_sleep=self.thread_sleep)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


class Pool:
    def __init__(
        self,
        process_pool: Union[None, bool, ThreadPoolExecutor,
                            ProcessPoolExecutor] = None,
        pool_worker: Optional[int] = None,
        aws_lambda: Optional[bool] = None,
    ) -> None:

        freeze_support()
        cpu = cpu_count()
        if process_pool is None:
            if pool_worker == 0:
                self.pool = None
                return
            process_pool = cpu > 1

        if isinstance(process_pool, bool):
            if process_pool:
                if (pool_worker is None) or (pool_worker == 0):
                    pool_worker = cpu
                elif pool_worker < 0:
                    pool_worker = max(1, pool_worker - cpu_count())

                try:
                    if aws_lambda:
                        self.pool = PipeProcessPoolExecutor(
                            max_worker=pool_worker)
                    else:
                        self.pool = StackTracedProcessPoolExecutor(
                            max_workers=pool_worker)
                except OSError:
                    self.pool = PipeProcessPoolExecutor(
                        max_worker=pool_worker)
            else:
                if (pool_worker is None) or (pool_worker == 0):
                    pool_worker = min(1 + (cpu * 4), 61)
                elif pool_worker < 0:
                    pool_worker = min(max(1, (4 * cpu) + 1 - pool_worker), 61)

                self.pool = StackTracedThreadPoolExecutor(
                    max_workers=pool_worker)

        else:
            self.pool = process_pool

    def __del__(self):
        if self.pool is None:
            self.pool.shutdown(wait=False)

    def submit(self, fn: Callable, *arg, **kw) -> Future:
        return self.pool.submit(fn, *arg, **kw)
