import asyncio
import time
import sys
import traceback

DEFAULT_RATE_LIMIT  = 5
DEFAULT_TIMERANGE_S = 1.0
DEFAULT_QUEUE_SIZE  = 10_000


async def worker(name, queue, time_range_s):
    # use name for debugging
    # time_range_s is the time range in seconds
    while True:
        routine = await queue.get()

        start_time_s = time.time()
        try:
            await routine
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)

        queue.task_done()

        end_time_s = time.time()
        delta_s = end_time_s - start_time_s

        if delta_s < time_range_s:
            sleep_for = time_range_s - delta_s
            await asyncio.sleep(sleep_for)

class RateLimiter:

    def __init__(self,
                 rate_limit: int        = DEFAULT_RATE_LIMIT,
                 time_range_s: float    = DEFAULT_TIMERANGE_S,
                 queue_max_size: int    = DEFAULT_QUEUE_SIZE):
        self.rate_limit = rate_limit
        self.time_range_s = time_range_s
        self.queue_max_size = queue_max_size

        self.queue = asyncio.Queue(self.queue_max_size)
        self.tasks = None

    async def start_if_not(self):
        if self.tasks is None:
            self.tasks = [
                asyncio.create_task(worker(f'worker-{i}', self.queue, self.time_range_s))
                for i in range(self.rate_limit)
            ]

    def send_task(self, routine):
        try:
            self.queue.put_nowait(routine)
            return True
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            return False

    async def submit(self, routine):
        await self.start_if_not()
        result = []
        event = asyncio.Event()
        async def task_wrapper():
            try:
                response = await routine
                result.append(response)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)
            event.set()
        self.send_task(task_wrapper())

        await event.wait()
        if len(result) == 1:
            return result[0]
        else:
            return None

    async def submit_batch(self, routine_batch):
        await self.start_if_not()
        batch = [self.submit(routine) for routine in routine_batch]
        return await asyncio.gather(*batch)

    async def close(self):
        await self.queue.join()
        if self.tasks is not None:
            for task in self.tasks:
                task.cancel()
            await asyncio.gather(*self.tasks, return_exceptions=True)


class RateLimitedBatchQueue:

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.batches = 0
        self.resolved_batches = 0

    async def add_batch_task(self, routine_batch, notify_batches_ahead = None):
        batch_id = self.batches
        batches_ahead = self.batches - self.resolved_batches
        self.batches += 1
        if notify_batches_ahead is not None:
            await notify_batches_ahead(batches_ahead)
        result = await self.rate_limiter.submit_batch(routine_batch)
        self.resolved_batches += 1
        return result