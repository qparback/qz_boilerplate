"""Smoke-test integration tests — verify both API and DB layers respond."""

from httpx import AsyncClient


async def test_hello_returns_fastapi_message(client: AsyncClient):
    response = await client.get("/v1/hello")
    assert response.status_code == 200
    body = response.json()
    assert body == {"message": "hello world from FastAPI", "source": "fastapi"}


async def test_hello_db_returns_seeded_message(client: AsyncClient):
    response = await client.get("/v1/hello/db")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "database"
    assert "hello world from db" in body["message"].lower()


async def test_hello_requires_api_key(client: AsyncClient):
    response = await client.get("/v1/hello", headers={"x-api-key": ""})
    assert response.status_code == 403
