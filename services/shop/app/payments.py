import asyncio
import random


class PaymentTimeout(Exception):
    def __init__(self, limit_ms: int):
        self.limit_ms = limit_ms


async def charge(timeout_ms: int) -> bool:
    latency = random.uniform(0.04, 0.14)
    try:
        await asyncio.wait_for(asyncio.sleep(latency), timeout_ms / 1000)
    except TimeoutError as error:
        raise PaymentTimeout(timeout_ms) from error
    return random.random() > 0.1
