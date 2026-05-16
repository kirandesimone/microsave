from pymongo.asynchronous.database import AsyncDatabase

async def create_indexes(db: AsyncDatabase):
    await db["saves"].create_index(
        [("client_app_id", 1), ("user_id", 1), ("save_slot", 1)],
        unique=True,
        name="unique_save_key",
    )

