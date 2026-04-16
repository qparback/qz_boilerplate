"""Pure-function tests for pagination helpers — no DB, no app."""

import pytest

from api.schemas.pagination import PageParams, PaginatedResponse


def test_offset_first_page():
    assert PageParams(page=1, page_size=20).offset == 0


def test_offset_later_pages():
    assert PageParams(page=2, page_size=20).offset == 20
    assert PageParams(page=3, page_size=10).offset == 20


def test_paginated_response_pages_calculation():
    resp = PaginatedResponse[int].create(items=[], total=45, params=PageParams(page=1, page_size=20))
    assert resp.pages == 3  # 45 / 20 = 2.25 → 3


def test_paginated_response_zero_total():
    resp = PaginatedResponse[int].create(items=[], total=0, params=PageParams(page=1, page_size=20))
    assert resp.pages == 0


@pytest.mark.parametrize(
    ("total", "page_size", "expected"),
    [(1, 20, 1), (20, 20, 1), (21, 20, 2), (100, 25, 4)],
)
def test_pages_ceiling_division(total: int, page_size: int, expected: int):
    resp = PaginatedResponse[int].create(items=[], total=total, params=PageParams(page=1, page_size=page_size))
    assert resp.pages == expected
