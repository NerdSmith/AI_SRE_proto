import logging
import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import settings
from .payments import PaymentTimeout, charge
from .pricing import calculator
from .storage import Pool, PoolExhausted, saver

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("shop.orders")

calculate_total = calculator(settings.version)
save_order = saver(settings.version)


class Order(BaseModel):
    customer: str
    amount: float
    promo: dict | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = Pool(settings.pool_size, settings.pool_wait_ms)
    log.info("release deployed version=%s previous=%s", settings.version, settings.previous_version)
    log.info("config loaded payment_timeout_ms=%s pool_size=%s", settings.payment_timeout_ms, settings.pool_size)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}


@app.post("/orders")
async def create_order(order: Order):
    order_id = uuid.uuid4().hex[:12]
    try:
        total = calculate_total(order.amount, order.promo)
        paid = await charge(settings.payment_timeout_ms)
        await save_order(app.state.pool, paid)
    except PaymentTimeout as error:
        log.error("payment gateway timeout order=%s limit_ms=%s", order_id, error.limit_ms)
        raise HTTPException(504, "payment timeout") from error
    except PoolExhausted as error:
        log.error(
            "db pool exhausted order=%s size=%s in_use=%s waited_ms=%s",
            order_id, error.size, error.in_use, error.waited_ms,
        )
        raise HTTPException(503, "database unavailable") from error
    except Exception as error:
        log.exception("order failed order=%s customer=%s", order_id, order.customer)
        raise HTTPException(500, "internal error") from error
    if not paid:
        log.warning("payment declined order=%s", order_id)
        raise HTTPException(402, "payment declined")
    log.info("order paid order=%s customer=%s total=%s", order_id, order.customer, total)
    return {"id": order_id, "total": total}
