import pytest
from httpx import AsyncClient
from order_offer_service.app.main import app
import order_offer_service.app.core.exceptions as exceptions
from order_offer_service.app.schemas.offers import OfferCreateRequest
from order_offer_service.app.schemas.orders import OrderStartRequest, OrderStopRequest


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_offer(monkeypatch):
    # Mock dependencies to isolate test
    async def mock_get_scooter(self, scooter_id):
        return {"scooter_id": scooter_id, "zone_id": "center", "available": True, "charge": 100}

    async def mock_get_zone(self, zone_id):
        return {"zone_id": zone_id, "price_multiplier": 15, "price_unlock": 50, "default_deposit": 1000, "offer_ttl_seconds": 300}

    async def mock_get_user(self, user_id):
        return {"user_id": user_id, "has_subscribtion": False, "trusted": False}

    async def mock_get_price_coeff_settings(self):
        return {"surge": 1.0, "low_charge_discount": 1.0}

    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.get_scooter", mock_get_scooter)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ZoneClient.get_zone", mock_get_zone)
    monkeypatch.setattr("order_offer_service.app.services.integrations.UserClient.get_user", mock_get_user)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ConfigClient.get_price_coeff_settings", mock_get_price_coeff_settings)

    payload = {"user_id": 1, "scooter_id": 101}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/api/v1/offers/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] > 0
    assert data["ttl"] > 0


@pytest.mark.asyncio
async def test_create_offer_pricing_logic(monkeypatch):
    async def mock_get_scooter(_):
        return {"zone_id": "center", "charge": 5}

    async def mock_get_zone(_):
        return {"price_multiplier": 10, "price_unlock": 50,
                "default_deposit": 200, "offer_ttl_seconds": 100}

    async def mock_get_user(_):
        return {"has_subscribtion": False, "trusted": True}

    async def mock_price_settings():
        return {"surge": 2.0, "low_charge_discount": 0.5}

    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.get_scooter", mock_get_scooter)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ZoneClient.get_zone", mock_get_zone)
    monkeypatch.setattr("order_offer_service.app.services.integrations.UserClient.get_user", mock_get_user)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ConfigClient.get_price_coeff_settings", mock_price_settings)

    payload = {"user_id": 1, "scooter_id": 123}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.put("/api/v1/offers/create", json=payload)

    assert r.status_code == 200
    body = r.json()
    # 10 * 2.0 surge = 20, then *0.5 low charge discount = 10
    assert body["price_per_minute"] == 10


@pytest.mark.asyncio
async def test_start_order_expired_offer(monkeypatch):
    async def mock_get_scooter(_, require_available=True):
        return {"zone_id": "center", "available": True}

    # force expire inside repo
    async def mock_get_valid_offer(session, offer_id, user_id):
        raise exceptions.OfferExpired()

    monkeypatch.setattr("order_offer_service.app.services.offers.OfferService.get_valid_offer", "get_valid_offer", mock_get_valid_offer)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.get_scooter", mock_get_scooter)

    payload = {"user_id": 1, "offer_id": 1}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.put("/api/v1/orders/start", json=payload)

    assert r.json()["message"] == "offer_expired"




@pytest.mark.asyncio
async def test_order_lifecycle(monkeypatch):
    # Mocks for scooter client and payment client
    async def mock_get_scooter(scooter_id, require_available=True):
        return {"scooter_id": scooter_id, "zone_id": "center", "available": True, "charge": 100}

    async def mock_lock_scooter(scooter_id):
        return None

    async def mock_unlock_scooter(scooter_id):
        return None

    async def mock_hold_money(user_id, order_id, amount):
        return None

    async def mock_clear_money(user_id, order_id, amount):
        return None

    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.get_scooter", mock_get_scooter)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.lock_scooter", mock_lock_scooter)
    monkeypatch.setattr("order_offer_service.app.services.integrations.ScooterClient.unlock_scooter", mock_unlock_scooter)
    monkeypatch.setattr("order_offer_service.app.services.integrations.PaymentClient.hold_money", mock_hold_money)
    monkeypatch.setattr("order_offer_service.app.services.integrations.PaymentClient.clear_money", mock_clear_money)

    # Create offer first
    payload_offer = {"user_id": 1, "scooter_id": 101}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        offer_resp = await ac.put("/api/v1/offers/create", json=payload_offer)
        offer_id = offer_resp.json()["offer_id"]

    # Start order
    payload_start = {"user_id": 1, "offer_id": offer_id}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        start_resp = await ac.put("/api/v1/orders/start", json=payload_start)
    assert start_resp.status_code == 200
    order_id = start_resp.json()["order_id"]

    # Get order info
    async with AsyncClient(app=app, base_url="http://test") as ac:
        get_resp = await ac.get("/api/v1/orders/get", params={"user_id": 1, "order_id": order_id})
    assert get_resp.status_code == 200
    assert get_resp.json()["order_id"] == order_id

    # Stop order
    payload_stop = {"user_id": 1, "order_id": order_id}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        stop_resp = await ac.put("/api/v1/orders/stop", json=payload_stop)
    assert stop_resp.status_code == 200
    assert "total_price" in stop_resp.json()
    assert "archive_key" in stop_resp.json()


@pytest.mark.asyncio
async def test_domain_error(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/error_domain")
    assert response.status_code == 404
