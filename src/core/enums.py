import enum


class TransactionStatus(str, enum.Enum):
    """Defines the possible statuses for a transaction."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    VALIDATED = "validated"
