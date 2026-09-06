"""Pagination dependency."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query

PageParamsDep = Annotated[int, Query(..., ge=1, description="Page number (1-based)")]


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> tuple[int, int]:
    """Return (page, page_size) with validated bounds."""
    return page, page_size