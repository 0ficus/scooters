import pytest
import time
import order_offer_service.app.core.exceptions as exceptions
from datetime import datetime, timezone, timedelta
from order_offer_service.app.dependencies import offer_service, order_service
from order_offer_service.app.schemas.orders import OrderStartRequest, OrderStopRequest


class MockOffer:
    def __init__(
        self,
        offer_id,
        user_id,
        scooter_id,
        price_per_minute,
        price_unlock,
        deposit,
        ttl,
    ):
        self.offer_id = offer_id
        self.user_id = user_id
        self.scooter_id = scooter_id
        self.price_per_minute = price_per_minute
        self.price_unlock = price_unlock
        self.deposit = deposit
        self.ttl = ttl
        self.time_offer_creation = datetime.now(timezone.utc)


class MockOfferRepo:
    def __init__(self):
        self.storage = {}
        self._next_id = 1   # auto-increment primary key simulator

    async def get(self, session, offer_id: int):
        return self.storage.get(offer_id)

    async def remove(self, session, offer_id: int):
        self.storage.pop(offer_id, None)

    async def delete_expired(self, session):
        now = datetime.now(timezone.utc)
        to_delete = []

        for offer_id, offer in self.storage.items():
            expires_at = offer.time_offer_creation + timedelta(seconds=offer.ttl)
            if expires_at < now:
                to_delete.append(offer_id)

        for offer_id in to_delete:
            self.storage.pop(offer_id, None)

        return len(to_delete)

    async def create(
        self,
        session,
        *,
        user_id: int,
        scooter_id: int,
        price_per_minute: int,
        price_unlock: int,
        deposit: int,
        ttl: int,
    ):
        offer_id = self._next_id
        self._next_id += 1

        offer = MockOffer(
            offer_id=offer_id,
            user_id=user_id,
            scooter_id=scooter_id,
            price_per_minute=price_per_minute,
            price_unlock=price_unlock,
            deposit=deposit,
            ttl=ttl,
        )

        self.storage[offer_id] = offer
        return offer

@pytest.mark.asyncio
async def test_get_valid_order(monkeypatch):
    repo = MockOfferRepo()
    monkeypatch.setattr(offer_service, "offer_repo", repo)

    # test no offer initially
    with pytest.raises(exceptions.OfferNotFound):
        await offer_service.get_valid_offer(None, 1, 1)
    offer = await repo.create(session=None,
                              user_id=1,
                              scooter_id=2,
                              price_per_minute=3,
                              price_unlock=4,
                              deposit=5,
                              ttl=2)
    # test offer in db
    assert offer == await offer_service.get_valid_offer(None, 1, 1)
    # test correctly handles incorrect user_id, but correct offer_id
    with pytest.raises(exceptions.OfferNotFound):
        await offer_service.get_valid_offer(None, 1, 2)
    time.sleep(2)
    # test expired offer case
    with pytest.raises(exceptions.OfferExpired):
        await offer_service.get_valid_offer(None, 1, 1)

@pytest.mark.asyncio
async def test_consume_offer(monkeypatch):
    repo = MockOfferRepo()
    monkeypatch.setattr(offer_service, "offer_repo", repo)

    offer = await repo.create(session=None,
                              user_id=1,
                              scooter_id=2,
                              price_per_minute=3,
                              price_unlock=4,
                              deposit=5,
                              ttl=2)
    assert offer == await offer_service.get_valid_offer(None, 1, 1)
    await offer_service.consume_offer(None, 1)
    # test offer removed by consume_offer
    with pytest.raises(exceptions.OfferNotFound):
        await offer_service.get_valid_offer(None, 1, 1)

class MockOrder:
    def __init__(
        self,
        order_id,
        user_id,
        scooter_id,
        price_per_minute,
        price_unlock,
        deposit,
        ttl,
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.scooter_id = scooter_id
        self.price_per_minute = price_per_minute
        self.price_unlock = price_unlock
        self.deposit = deposit
        self.ttl = ttl
        self.time_start = datetime.now(timezone.utc)
        self.time_finish = None

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "scooter_id": self.scooter_id,
            "price_per_minute": self.price_per_minute,
            "price_unlock": self.price_unlock,
            "deposit": self.deposit,
            "ttl": self.ttl,
            "time_start": self.time_start.isoformat(),
            "time_finish": self.time_finish.isoformat() if self.time_finish else None,
        }


class MockOrderRepo:
    def __init__(self):
        self.storage = {}
        self._next_id = 1

    async def create(self, session, **kwargs):
        order_id = self._next_id
        self._next_id += 1
        order = MockOrder(order_id=order_id, **kwargs)
        self.storage[order_id] = order
        return order

    async def get(self, session, order_id):
        return self.storage.get(order_id)

    async def finish(self, session, order_id):
        order = self.storage.get(order_id)
        if order:
            order.time_finish = datetime.now(timezone.utc)
        return order

    async def delete(self, session, order_id):
        self.storage.pop(order_id, None)

class MockPaymentClient:
    def __init__(self):
        self.holds = []
        self.cleared = []

    async def hold_money(self, user_id, order_id, amount):
        if amount < 0:
            raise exceptions.PaymentDeclined()
        self.holds.append((user_id, order_id, amount))

    async def clear_money(self, user_id, order_id, amount):
        self.cleared.append((user_id, order_id, amount))


class MockScooterClient:
    def __init__(self):
        self.locked = []
        self.unlocked = []

    async def lock_scooter(self, scooter_id):
        if scooter_id == -1:
            raise exceptions.ScooterUnavailable()
        self.locked.append(scooter_id)

    async def unlock_scooter(self, scooter_id):
        self.unlocked.append(scooter_id)


class MockSession:
    async def commit(self):
        return None



@pytest.mark.asyncio
async def test_start_order(monkeypatch):
    order_repo = MockOrderRepo()
    payment = MockPaymentClient()
    scooter = MockScooterClient()
    session = MockSession()
    
    class MockOfferService:
        async def get_offer(self, offer_id):
            return type('Offer', (), {
                'scooter_id': 5,
                'price_per_minute': 10,
                'price_unlock': 2,
                'deposit': 5,
                'ttl': 3600,
                'time_created': datetime.now(timezone.utc)
            })()

    offer_service = MockOfferService()

    monkeypatch.setattr(order_service, "order_repo", order_repo)
    monkeypatch.setattr(order_service, "offer_service", None)
    monkeypatch.setattr(order_service, "payment_client", payment)
    monkeypatch.setattr(order_service, "scooter_client", scooter)

    req = OrderStartRequest(user_id=1, offer_id=123)
    order_id = await svc.start_order(session, req)

    assert order_id == 1
    assert order_repo.storage[order_id].user_id == 1
    assert payment.holds == [(1, order.order_id, 5)]
    assert scooter.locked == [5]


@pytest.mark.asyncio
async def test_stop_order(monkeypatch):
    order_repo = MockOrderRepo()
    payment = MockPaymentClient()
    scooter = MockScooterClient()
    session = MockSession()


    # Create service
    monkeypatch.setattr(order_service, "order_repo", order_repo)
    monkeypatch.setattr(order_service, "offer_service", None)
    monkeypatch.setattr(order_service, "payment_client", payment)
    monkeypatch.setattr(order_service, "scooter_client", scooter)

    # Create order
    order = await order_repo.create(
        None,
        user_id=1,
        scooter_id=5,
        price_per_minute=60,   # 1 unit per second (simplifies math)
        price_unlock=10,
        deposit=5,
        ttl=2,
    )

    # Mock S3
    archive_keys = []

    async def mock_store(self, data, ttl):
        archive_keys.append("archived")
        return "archived"

    monkeypatch.setattr("order_offer_service.app.core.s3.S3Storage.store_order", mock_store)

    # Simulate time passage
    await order_repo.finish(None, order.order_id)
    order.time_start -= timedelta(seconds=120)  # 2 minutes duration

    req = OrderStopRequest(order_id=order.order_id, user_id=1)

    total, key = await order_service.stop_order(session, req)

    assert total == 120 + 10
    assert payment.cleared == [(1, order.order_id, total)]
    assert scooter.unlocked == [5]
    assert key == "archived"
    assert order.order_id not in order_repo.storage
