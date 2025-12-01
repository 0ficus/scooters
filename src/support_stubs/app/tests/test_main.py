import pytest
from httpx import AsyncClient, ASGITransport
from support_stubs.app.main import app


@pytest.mark.asyncio
async def test_get_price_coeff_settings():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        response = await ac.get("/configs/price_coeff_settings")
    assert response.status_code == 200
    assert "surge" in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("zone_id, expected_status", [("center", 200), ("unknown", 404)])
async def test_get_zone(zone_id, expected_status):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        response = await ac.get(f"/zones/{zone_id}")
    assert response.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id, expected_status", [(1, 200), (999, 404)])
async def test_get_user(user_id, expected_status):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        response = await ac.get(f"/users/{user_id}")
    assert response.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize("scooter_id, expected_status", [(101, 200), (999, 404)])
async def test_get_scooter(scooter_id, expected_status):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        response = await ac.get(f"/scooters/{scooter_id}")
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_lock_unlock_scooter():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        # Lock scooter 101
        response = await ac.put("/scooters/101/lock")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Unlock scooter 101
        response = await ac.put("/scooters/101/unlock")
        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_hold_and_clear_payments():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        # Hold payment for unknown user should fail
        response = await ac.put("/payments/13/999/hold", params={"amount": 10.0})
        assert response.status_code == 404
        assert "user_not_found" in response.json()["detail"]

        # Hold payment for user 1, order 999
        response = await ac.put("/payments/1/999/hold", params={"amount": 10.0})
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Holding again for same order should success
        response = await ac.put("/payments/1/999/hold", params={"amount": 10.0})
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Clear payment for unknown user should fail
        response = await ac.put("/payments/13/999/clear", params={"amount": 10.0})
        assert response.status_code == 404
        assert "user_not_found" in response.json()["detail"]

        # Clear payment
        response = await ac.put("/payments/1/999/clear", params={"amount": 10.0})
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Clear payment again should success
        response = await ac.put("/payments/1/999/clear", params={"amount": 10.0})
        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
