from pymongo.asynchronous.database import AsyncDatabase

from microsave_app.models.save import SaveDocument


async def upsert_save(sd: SaveDocument, db: AsyncDatabase):
    doc = sd.model_dump()

    await db["saves"].update_one(
        {
            "client_app_id": sd.client_app_id,
            "user_id": sd.user_id,
            "save_slot": sd.save_slot,
        },
        {"$set": doc},
        upsert=True,
    )


async def get_save(client_app_id: str, user_id: str, save_slot:str, db: AsyncDatabase):
    return await db["saves"].find_one(
        {
            "client_app_id": client_app_id,
            "user_id": user_id,
            "save_slot": save_slot,
        }
    )
