from fastapi import status


class DomainError(Exception):
    message: str = "domain_error"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class OfferNotFound(DomainError):
    message = "offer_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class OfferExpired(DomainError):
    message = "offer_expired"


class OrderNotFound(DomainError):
    message = "order_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class PaymentDeclined(DomainError):
    message = "payment_declined"
    status_code = status.HTTP_402_PAYMENT_REQUIRED


class ScooterUnavailable(DomainError):
    message = "scooter_unavailable"


class ExternalServiceError(DomainError):
    message = "external_service_error"
    status_code = status.HTTP_502_BAD_GATEWAY

