"""Enums for the QR Code Ordering System"""

from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    CANCELED = "canceled"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class UserRole(str, Enum):
    """User role enumeration"""
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"