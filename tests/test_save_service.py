import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from microsave_app.models.save import SaveDocument
from microsave_app.services.mongo import upsert_save


@pytest.mark.asyncio
async def test_upsert_save_calls():
    # Mock the DB and the collection
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_db.__getitem__.return_value = mock_collection

    # Test data
    now = datetime.now(timezone.utc)
    save_doc = SaveDocument(
        client_app_id="scavenger",
        user_id="user_123",
        save_slot="slot_1",
        schema_version=1,
        payload={"data": "some-save-data"},
        created_at=now,
        updated_at=now,
    )

    await upsert_save(save_doc, mock_db)

    # Verify the mock assertion
    mock_collection.update_one.assert_called_once()

    args, kwargs = mock_collection.update_one.call_args
    query_filter = args[0]
    update_doc = args[1]

    # Verify filter
    assert query_filter["client_app_id"] == "scavenger"
    assert query_filter["user_id"] == "user_123"

    # Verify update operators
    assert "$set" in update_doc
    assert "$setOnInsert" in update_doc

    # Verify created_at is only in $setOnInsert
    assert "created_at" in update_doc["$setOnInsert"]
    assert "created_at" not in update_doc["$set"]

    # Verify upsert=True was passed
    assert kwargs["upsert"] is True
