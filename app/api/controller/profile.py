from fastapi import Depends, Response
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.services.profiles import get_all_users, seed_users_using_seed_json_file
from typing import Optional


async def get_all_users_controller(
    db: Session = Depends(get_db),
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    limit: Optional[int] = None,
    page: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
):
    return await get_all_users(
        db, gender, age_group, country_id,
        min_age, max_age,
        min_gender_probability, min_country_probability,
        limit, page, sort_by, order
    )

async def seed_users_controller(db: Session = Depends(get_db)):
    return await seed_users_using_seed_json_file(db, "seed_profiles.json")