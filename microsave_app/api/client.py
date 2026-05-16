from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase 

from microsave_app.models.save import SaveEnvelope, SaveResponse
from microsave_app.helpers.save import build_save_document
from microsave_app.services.mongo import upsert_save, get_save
from microsave_app.core.mongo import get_db


router = APIRouter()

@router.post("/save", response_model=SaveResponse, status_code=200)
async def save(se: SaveEnvelope, db: AsyncDatabase = Depends(get_db)) -> SaveResponse:
    sd = build_save_document(se)
    await upsert_save(sd, db)

    return SaveResponse(
        client_app_id = sd.client_app_id,
        user_id = sd.user_id,
        save_slot = sd.save_slot,
        schema_version = sd.schema_version,
        updated_at = sd.updated_at,
        payload = sd.payload,
    )


@router.get("/load/{client_app_id}/{user_id}/{save_slot}", response_model=SaveResponse)
async def load(
        client_app_id: str, 
        user_id: str, 
        save_slot: str, 
        db: AsyncDatabase = Depends(get_db)
) -> SaveResponse:
    sd = await get_save(client_app_id, user_id, save_slot, db)

    if sd is None:
        raise HTTPException(status_code=404, detail="Save not found")

    return SaveResponse(**sd)



