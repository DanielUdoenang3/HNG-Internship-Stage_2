from pydantic import BaseModel, field_validator


class UserProfile(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Missing or empty name")
        return v
