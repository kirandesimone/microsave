import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI

from microsave_app.helpers.indexes import create_indexes
from microsave_app.core.config import Settings, get_settings
from microsave_app.core.mongo import create_mongo_client
from microsave_app.api.client import router as client_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = getattr(app.state, "settings", get_settings())
    client = await create_mongo_client(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    app.state.mongo_client = client
    app.state.db = db

    await create_indexes(db)

    yield

    await client.close()


def create_app(settings: Settings = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan,
    )

    app.state.settings = app_settings
    app.include_router(client_router)
    return app


app = create_app()


def main():
    uvicorn.run("microsave_app.main:app", reload=True)


if __name__ == "__main__":
    main()
