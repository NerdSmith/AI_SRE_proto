import asyncio


class PoolExhausted(Exception):
    def __init__(self, size: int, in_use: int, waited_ms: int):
        self.size = size
        self.in_use = in_use
        self.waited_ms = waited_ms


class Pool:
    def __init__(self, size: int, wait_ms: int):
        self.size = size
        self.wait_ms = wait_ms
        self.in_use = 0
        self._slots = asyncio.Semaphore(size)

    async def acquire(self) -> None:
        try:
            await asyncio.wait_for(self._slots.acquire(), self.wait_ms / 1000)
        except TimeoutError as error:
            raise PoolExhausted(self.size, self.in_use, self.wait_ms) from error
        self.in_use += 1

    def release(self) -> None:
        self.in_use -= 1
        self._slots.release()


async def save_stable(pool: Pool, paid: bool) -> None:
    await pool.acquire()
    try:
        await asyncio.sleep(0.005)
    finally:
        pool.release()


async def save_with_early_return(pool: Pool, paid: bool) -> None:
    await pool.acquire()
    await asyncio.sleep(0.005)
    if not paid:
        return
    pool.release()


def saver(version: str):
    return save_with_early_return if version == "2.5.0" else save_stable
