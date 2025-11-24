CREATE TABLE IF NOT EXISTS offers (
    offer_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scooter_id INTEGER NOT NULL,
    time_offer_creation TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    ttl INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_offers_user ON offers (user_id);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scooter_id INTEGER NOT NULL,
    time_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    time_finish TIMESTAMPTZ NULL,
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    ttl INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id);

