import pytest

from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from microsave_app.main import create_app
from microsave_app.core.config import Settings, get_settings


def get_test_settings():
    return Settings(_env_file=".env.test.mongodb")


@pytest.fixture()
def client(test_app, connect_db):
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture()
def test_app():
    app = create_app()
    app.dependency_overrides[get_settings] = get_test_settings
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
async def connect_db():
    settings = get_test_settings();
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        await client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")

    except Exception as e:
        raise Exception("Unable to find the document due to the following error: ", e)

    await db["saves"].delete_many({})
    yield
    await db["saves"].delete_many({})
    await client.close()

