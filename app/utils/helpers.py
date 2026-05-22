"""Reusable small utility functions."""

import math


def compute_pages(total: int, size: int) -> int:
    """Calculate total number of pages."""
    if size <= 0:
        return 0
    return math.ceil(total / size)
