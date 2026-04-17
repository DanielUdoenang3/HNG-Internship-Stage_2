from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models.base_models import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    gender_probability = Column(String, nullable=False)
    sample_size = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(String, nullable=False)
    country_id = Column(String, nullable=False)
    country_probality = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(name='{self.name}', gender='{self.gender}')>"