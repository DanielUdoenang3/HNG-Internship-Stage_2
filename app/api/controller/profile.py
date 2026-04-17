from fastapi import Depends, Response
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.schema.profile import UserProfile
from app.services.profiles import create_user, get_user, get_all_users, delete_user
from typing import Optional


async def create_user_controller(data: UserProfile, db: Session = Depends(get_db)):
    return await create_user(data, db)


async def get_user_controller(id: str, db: Session = Depends(get_db)):
    return await get_user(id, db)


async def get_all_users_controller(
    db: Session = Depends(get_db),
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
):
    return await get_all_users(db, gender, country_id, age_group)


async def delete_user_controller(id: str, db: Session = Depends(get_db), response: Response = None):
    result = await delete_user(id, db)
    if result is None:
        response.status_code = 204
        return response
    return result
