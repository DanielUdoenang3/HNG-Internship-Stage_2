from sqlalchemy import Column, Integer, String, Float
from app.models.base_models import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    name = Column(String, nullable=False, unique=True, index=True)
    gender = Column(String, nullable=False)
    gender_probability = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(String, nullable=False)
    country_id = Column(String(2), nullable=False)
    country_name = Column(String, nullable=False)
    country_probability = Column(Float, nullable=False)

    def __repr__(self):
        return f"<User(name='{self.name}', gender='{self.gender}')>"
