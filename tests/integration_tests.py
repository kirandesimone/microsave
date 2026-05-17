import pytest
from pathlib import Path

from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from microsave_app.main import create_app
from microsave_app.core.config import Settings, get_settings

BASE_DIR = Path(__file__).resolve().parents[1]


def get_test_settings():
    return Settings(_env_file=BASE_DIR / ".env.test.mongodb")


@pytest.fixture()
def client(test_app, connect_db):
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture()
def test_app():
    test_settings = get_test_settings()
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_settings] = get_test_settings
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
async def connect_db():
    settings = get_test_settings()
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        await client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")

    except Exception as e:
        raise Exception(
            "Unable to find the document due to the following error: ", e
        )

    await db["saves"].delete_many({})
    yield
    await db["saves"].delete_many({})
    await client.close()


@pytest.mark.asyncio
async def test_save_load_and_delete_lifecycle(client):
    """
    Test Create, Read, and Delete a save.
    """
    payload = {
        "client_app_id": "scavenger",
        "user_id": "integration_test_user",
        "save_slot": "slot_1",
        "schema_version": 1,
        "payload": {"data": "initial save state"},
    }
    # 1. POST /save
    response = client.post("/save", json=payload)
    assert response.status_code == 200
    assert response.json()["payload"]["data"] == "initial save state"

    # 2. GET /load
    response = client.get("/load/scavenger/integration_test_user/slot_1")
    assert response.status_code == 200
    assert response.json()["payload"]["data"] == "initial save state"

    # 3. DELETE /delete
    response = client.delete("/delete/scavenger/integration_test_user/slot_1")
    assert response.status_code == 204

    # 4. GET /load (Verify it's deleted)
    response = client.get("/load/scavenger/integration_test_user/slot_1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_non_existent_save(client):
    """
    Verify that deleting a non-existent save returns 404.
    """
    response = client.delete("/delete/scavenger/nobody/nowhere")
    assert response.status_code == 404
