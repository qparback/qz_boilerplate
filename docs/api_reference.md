# API reference

The interactive Swagger UI is the source of truth: visit `/api/docs` once
the stack is running. This document covers conventions that apply across
endpoints.

## Authentication

Every `/api/v1/*` route requires the header:

```
x-api-key: <your-key>
```

A missing or wrong key returns `403 Forbidden`. The `/health` endpoint and
`/admin/*` are not gated by API key.

## Conventions

| Concern         | Convention                                                  |
| --------------- | ----------------------------------------------------------- |
| IDs             | UUID v4, returned as string in responses                    |
| Timestamps      | ISO 8601 with timezone (`2026-04-16T13:45:00+00:00`)        |
| Pagination      | `?page=1&page_size=20`, response wrapped in `PaginatedResponse` |
| Error format    | `{"error": "...", "detail": ..., "request_id": "..."}`      |
| Request ID      | Returned in `X-Request-ID` header on every response         |

## Pagination envelope

```json
{
  "items": [ ... ],
  "total": 137,
  "page": 1,
  "page_size": 20,
  "pages": 7
}
```

## Adding a new endpoint

See [CLAUDE.md — Adding a new resource](../CLAUDE.md#adding-a-new-resource-pattern-to-follow)
for the strict 4-file pattern.
