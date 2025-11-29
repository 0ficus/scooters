from __future__ import annotations

from fastapi import FastAPI, HTTPException

app = FastAPI(title="SupportStubsService", version="1.0.0")

ZONES = {
    "center": {"zone_id": "center", "price_multiplier": 15, "price_unlock": 52, "default_deposit": 993, "offer_ttl_seconds": 600},
    "suburb": {"zone_id": "suburb", "price_multiplier": 17, "price_unlock": 42, "default_deposit": 1000, "offer_ttl_seconds": 500},
}

USERS = {
    1: {
        "user_id": 1,
        "has_subscribtion": True,
        "trusted": True,
        "bill": 0.0,
        "orders": {
            0: {"hold_bill": 0.0},
            1: {"hold_bill": 10.0},
        }
    },
    2: {
        "user_id": 2,
        "has_subscribtion": False,
        "trusted": False,
        "bill": 0.0,
        "orders": {
            0: {"hold_bill": 42.0},
            1: {"hold_bill": 1.0},
        }
    },
}

SCOOTERS = {
    101: {"scooter_id": 101, "zone_id": "center", "available": True, "charge": 92},
    102: {"scooter_id": 102, "zone_id": "suburb", "available": True, "charge": 55},
}

CONFIG = {
    "price_coeff_settings": {"surge": 2, "low_charge_discount": 0.75}
}


@app.get("/configs/price_coeff_settings")
async def get_price_coeff_settings():
    return CONFIG["price_coeff_settings"]


@app.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    zone = ZONES.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="zone_not_found")
    return zone


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


@app.get("/scooters/{scooter_id}")
async def get_scooter(scooter_id: int):
    scooter = SCOOTERS.get(scooter_id)
    if not scooter:
        raise HTTPException(status_code=404, detail="scooter_not_found")
    return scooter


@app.put("/scooters/{scooter_id}/lock")
async def lock_scooter(scooter_id: int):
    scooter = SCOOTERS.get(scooter_id)
    if not scooter:
        raise HTTPException(status_code=404, detail="scooter_not_found")

    scooter["available"] = False
    return {"success": True}


@app.put("/scooters/{scooter_id}/unlock")
async def unlock_scooter(scooter_id: int):
    scooter = SCOOTERS.get(scooter_id)
    if not scooter:
        raise HTTPException(status_code=404, detail="scooter_not_found")

    scooter["available"] = True
    return {"success": True}


@app.put("/payments/{user_id}/{order_id}/hold")
async def hold_payments(user_id: int, order_id: int, amount: float):
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    orders = user.setdefault("orders", {})
    if order_id in orders:
        raise HTTPException(status_code=409, detail="order_payment_already_hold")

    orders[order_id] = {"hold_bill": amount}
    user["bill"] = user.get("bill", 0.0) - amount

    return {"success": True}


@app.put("/payments/{user_id}/{order_id}/clear")
async def clear_payments(user_id: int, order_id: int, amount: float):
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    orders = user.get("orders", {})
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")

    amount -= order.get("hold_bill", 0.0)
    orders.pop(order_id)
    user["bill"] = user.get("bill", 0.0) - amount

    return {"success": True}


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

