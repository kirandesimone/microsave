from fastapi import Request
from pymongo import AsyncMongoClient

async def create_mongo_client(uri: str) -> AsyncMongoClient:
    client = AsyncMongoClient(uri)

    try:
        await client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")

    except Exception as e:
        raise Exception("Unable to find the document due to the following error: ", e)

    return client

def get_db(request: Request):
    return request.app.state.db
