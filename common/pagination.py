"""Pagination standardisée pour toutes les listes API (< 2s QoS)."""
from __future__ import annotations

from typing import Any


def paginate_queryset(qs, page: int = 1, page_size: int = 20, max_page_size: int = 100):
    page = max(1, int(page or 1))
    page_size = min(max(1, int(page_size or 20)), max_page_size)
    total = qs.count()
    offset = (page - 1) * page_size
    items = list(qs[offset:offset + page_size])
    total_pages = (total + page_size - 1) // page_size if total else 0
    meta: dict[str, Any] = {
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
    }
    return items, meta


def paginated_response(items: list, meta: dict) -> dict:
    return {'items': items, 'pagination': meta}


def paginate_and_map(qs, serializer, page: int = 1, page_size: int = 20, max_page_size: int = 100):
    """Pagine un queryset et sérialise chaque élément."""
    rows, meta = paginate_queryset(qs, page, page_size, max_page_size)
    return paginated_response([serializer(row) for row in rows], meta)
