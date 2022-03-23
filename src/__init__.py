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
    _global_shutdown_lock,
    _shutdown,
)

import gc
from logging import Logger, getLogger
from multiprocessing import Pipe, freeze_support, get_context, cpu_count
from multiprocessing.connection import Connection
from typing import Any, Callable, Iterable, List, Mapping, Optional, Tuple, Union

gc.enable()


class MapFuture:
    futures: List[Future]

    def __init__(self) -> None:
        super().__init__()
        self.futures = []

    def result(self, timeout: Union[float, None] = None) -> Iterable:
        if len(self.futures) <= 0:
            return []

        return [i.result(timeout) for i in self.futures]

    def done(self, agg: Callable[[Iterable], Any] = all) -> Any:
        """gather done of Futures

        Args:
            agg (Callable[[Iterable], Any], optional): Aggregate function i.e. all, any, sum, list. Defaults to all.

        Returns:
            Any: Depend on agg function
        """
        return agg(i.done() for i in self.futures)


class AWSMultiPoolFuture(Future):
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
        future: AWSMultiPoolFuture,
        fn: Callable,
        logger: Logger,
        args,
        kwargs,
        mp_method: Optional[str] = None,
        thread_sleep: Optional[float] = 0.001
    ):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.logger = logger
        self.mp_method = mp_method

        if (thread_sleep) and (thread_sleep > 0):
            self.THREAD_SLEEP = thread_sleep

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            main, sub = Pipe()
            proc = get_context(self.mp_method).Process(
                target=self.process_worker,
                args=[self.fn, sub, self.logger] + list(self.args),
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

                    self.logger.info(status, **kws)
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

        except BaseException as exc:
            self.logger.exception('Exception from run process: {}', exc)
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None

    @staticmethod
    def process_worker(fn: Callable, pipe: Connection, logger: Logger, /, *arg, **kw):
        try:
            result = fn(*arg, **kw)
            pipe.send([True, result])
        except Exception as e:
            logger.exception("{e} from {fn}(*{arg},**{kw})",
                             e=e, fn=fn, arg=arg, kw=kw)
            pipe.send([False, e])

        pipe.close()
        return gc.collect()


class AWSLambdaMultiPoolExecutor(ThreadPoolExecutor):
    def __init__(
        self,
        max_workers: Union[int, None] = None,
        thread_name_prefix: Optional[str] = None,
        initializer: Optional[Callable[..., None]] = None,
        initargs: Optional[Tuple[Any, ...]] = None,
        logger: Optional[Logger] = None,
        mp_method: Optional[str] = None,
    ) -> None:

        if max_workers is None:
            max_workers = 1 + (cpu_count() * 2)

        super().__init__(max_workers, thread_name_prefix, initializer, initargs)
        self.logger = getLogger() if (logger is None) else logger
        self.mp_method = mp_method

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        with self._shutdown_lock, _global_shutdown_lock:
            if self._broken:
                raise BrokenThreadPool(self._broken)

            if self._shutdown:
                raise RuntimeError(
                    "cannot schedule new futures after shutdown")
            if _shutdown:
                raise RuntimeError(
                    "cannot schedule new futures after interpreter shutdown"
                )

            f = AWSMultiPoolFuture()
            w = _ProcessWorkItem(f, fn, self.logger, args,
                                 kwargs, self.mp_method)

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
                        self.pool = AWSLambdaMultiPoolExecutor(
                            max_worker=pool_worker)
                    else:
                        self.pool = ProcessPoolExecutor(
                            max_workers=pool_worker)
                except OSError:
                    self.pool = AWSLambdaMultiPoolExecutor(
                        max_worker=pool_worker)
            else:
                if (pool_worker is None) or (pool_worker == 0):
                    pool_worker = min(1 + (cpu * 4), 61)
                elif pool_worker < 0:
                    pool_worker = min(max(1, (4 * cpu) + 1 - pool_worker), 61)

                self.pool = ThreadPoolExecutor(max_workers=pool_worker)

        else:
            self.pool = process_pool

    def __del__(self):
        if self.pool is None:
            self.pool.shutdown(wait=False)

    def submit(self, fn: Callable, *arg, **kw) -> Future:
        return self.pool.submit(fn, *arg, **kw)

    def automap_async(self, fn: Callable, args_kw: Iterable):
        futures = MapFuture()

        for i in args_kw:
            if isinstance(i, Mapping):
                futures.futures.append(self.pool.submit(fn, **i))
            elif isinstance(i, Iterable):
                futures.futures.append(self.pool.submit(fn, *i))
            else:
                futures.futures.append(self.pool.submit(fn, i))

        return futures

    def map_async(self, fn: Callable, args_kw: Iterable):
        futures = MapFuture()

        for i in args_kw:
            futures.futures.append(self.pool.submit(fn, i))

        return futures
