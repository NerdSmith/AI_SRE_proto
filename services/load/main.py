import asyncio
import os
import random

import httpx

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8000/orders")
RPS = float(os.getenv("RPS", "15"))


def build_order() -> dict:
    user = random.randint(1000, 9999)
    promo = {"percent": random.choice([5, 10, 15])} if random.random() < 0.3 else None
    return {
        "customer": f"user{user}@example.com",
        "amount": round(random.uniform(300, 9000), 2),
        "promo": promo,
    }


async def send(client: httpx.AsyncClient) -> None:
    try:
        await client.post(TARGET_URL, json=build_order())
    except httpx.HTTPError:
        pass


async def main() -> None:
    tasks: set[asyncio.Task] = set()
    async with httpx.AsyncClient(timeout=3) as client:
        while True:
            task = asyncio.create_task(send(client))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            await asyncio.sleep(1 / RPS)


if __name__ == "__main__":
    asyncio.run(main())
