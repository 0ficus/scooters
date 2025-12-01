# Testing Record for Scooter Rental Services

## Date: 2024-06-XX  
## Environment: Local Docker Compose and CI Pipeline

---

### Support Stubs Service

| Test Case                                      | Result | Notes                                  |
|-----------------------------------------------|--------|----------------------------------------|
| GET /configs/price_coeff_settings              | Pass   | Returns surge and discount coefficients |
| GET /zones/{zone_id}                           | Pass   | Valid and invalid zone_id tested       |
| GET /users/{user_id}                           | Pass   | Valid and invalid user_id tested       |
| GET /scooters/{scooter_id}                     | Pass   | Valid and invalid scooter_id tested    |
| PUT /scooters/{scooter_id}/lock and unlock    | Pass   | Idempotency and error cases tested     |
| PUT /payments/{user_id}/{order_id}/hold        | Pass   | Hold payment, zero/negative amount, unknown order tested |
| PUT /payments/{user_id}/{order_id}/clear       | Pass   | Clear payment, including non-held order tested |
| GET /health                                    | Pass   | Returns status ok                       |

---

### Order Offer Service API

| Test Case                 | Result | Notes            |
|---------------------------|--------|------------------|
| PUT /api/v1/offers/create | Pass   | Valid, pricing logic tested |
| PUT /api/v1/orders/start  | Pass   | Valid, expired offer |
| GET /api/v1/orders/get    | Pass   | Valid input case |
| Happy path                | Pass   |                  |
| Domain error handling     | Pass   | Correct HTTP status and messages |
| GET /health               | Pass   | Returns status ok |

---

### Service Layer

| Test Case                                      | Result | Notes                                  |
|-----------------------------------------------|--------|----------------------------------------|
| OfferService.get_valid_offer                   | Pass   | Expired and valid offers tested        |
| OfferService.consume_offer                      | Pass   | Offer removal tested                    |
| OrderService.start_order                        | Pass   | Scooter lock and payment hold tested   |
| OrderService.stop_order                         | Pass   | Payment clear, scooter unlock, archiving tested |

---

## Summary

All critical paths and edge cases have been tested successfully in local and containerized environments.
---
