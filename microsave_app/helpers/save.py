from datetime import datetime, timezone

from microsave_app.models.save import SaveEnvelope, SaveDocument


def build_save_document(se: SaveEnvelope) -> SaveDocument:
    now = datetime.now(timezone.utc)
    return SaveDocument(
        **se.model_dump(),
        created_at=now,
        updated_at=now
    )
