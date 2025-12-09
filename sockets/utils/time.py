"""
Time utilities for Live Quiz Socket.IO Server
"""

from datetime import datetime, timedelta
from typing import Optional


class TimeUtils:
    """Utility class for time-related operations in quiz sessions."""

    @staticmethod
    def now() -> datetime:
        """Get current UTC datetime."""
        return datetime.utcnow()

    @staticmethod
    def add_seconds(dt: datetime, seconds: int) -> datetime:
        """Add seconds to a datetime object."""
        return dt + timedelta(seconds=seconds)

    @staticmethod
    def is_expired(deadline: Optional[datetime]) -> bool:
        """Check if a deadline has passed."""
        if deadline is None:
            return True
        return datetime.utcnow() > deadline

    @staticmethod
    def seconds_remaining(deadline: Optional[datetime]) -> int:
        """Calculate seconds remaining until deadline."""
        if deadline is None:
            return 0
        remaining = (deadline - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    @staticmethod
    def calculate_deadline(seconds: int) -> datetime:
        """Calculate deadline from now + seconds."""
        return datetime.utcnow() + timedelta(seconds=seconds)
