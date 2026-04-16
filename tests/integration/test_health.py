"""Integration tests covering the public health endpoint and API-key gating."""

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


async def test_protected_route_with_valid_key(client: AsyncClient):
    response = await client.get("/v1/_auth_check")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_protected_route_without_key(client: AsyncClient):
    # Override the default x-api-key header that the fixture installs.
    response = await client.get("/v1/_auth_check", headers={"x-api-key": ""})
    assert response.status_code == 403


async def test_protected_route_with_wrong_key(client: AsyncClient):
    response = await client.get("/v1/_auth_check", headers={"x-api-key": "wrong-key"})
    assert response.status_code == 403
