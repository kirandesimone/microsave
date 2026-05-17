from pydantic import BaseModel


class ScavengerPayload(BaseModel):
    data: str
