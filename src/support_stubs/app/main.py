from __future__ import annotations

from fastapi import FastAPI, HTTPException

app = FastAPI(title="SupportStubsService", version="1.0.0")

ZONES = {
    "center": {"zone_id": "center", "price_multiplier": 15, "price_unlock": 52, "default_deposit": 993, "offer_ttl_seconds": 600},
    "suburb": {"zone_id": "suburb", "price_multiplier": 17, "price_unlock": 42, "default_deposit": 1000, "offer_ttl_seconds": 500},
}

USERS = {
    1: {"user_id": 1, "has_subscribtion": True, "trusted": True},
    2: {"user_id": 2, "has_subscribtion": False, "trusted": False},
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

# TODO: payments


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

