import json
import re

from app.models.base import User
from sqlalchemy.orm import Session
from app.utils.custom_response import (
    error_response,
    success_response,
    success_list_response,
)
from app.utils.query_parser import parse_query
from fastapi import status


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "gender": user.gender,
        "gender_probability": user.gender_probability,
        "age": user.age,
        "age_group": user.age_group,
        "country_id": user.country_id,
        "country_name": user.country_name,
        "country_probability": user.country_probability,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

async def seed_users_using_seed_json_file(db: Session, seed_file_path: str) -> dict:
    try:
        with open(seed_file_path, "r") as f:
            users_data = json.load(f)

        profiles = users_data.get("profiles", users_data) if isinstance(users_data, dict) else users_data

        for user_data in profiles:
            user = User(
                name=user_data["name"],
                gender=user_data["gender"],
                gender_probability=user_data["gender_probability"],
                age=user_data["age"],
                age_group=user_data["age_group"],
                country_id=user_data["country_id"],
                country_name=user_data["country_name"],
                country_probability=user_data["country_probability"],
            )
            db.add(user)
        db.commit()
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Users seeded successfully"
        )
    except Exception as e:
        db.rollback()
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to seed users"
        )


async def get_all_users(
    db: Session, 
    gender: str = None, 
    age_group: str = None, 
    country_id: str = None, 
    min_age: int = None, 
    max_age: int = None, 
    min_gender_probability: float = None, 
    min_country_probability: float = None,
    limit: int = None,
    page: int = None,
    sort_by: str = None,
    order: str = None
) -> dict:
    query = db.query(User)

    if gender:
        query = query.filter(User.gender == gender.lower())
    if country_id:
        query = query.filter(User.country_id == country_id.upper())
    if age_group:
        query = query.filter(User.age_group == age_group.lower())
    if min_age is not None:
        query = query.filter(User.age >= min_age)
    if max_age is not None:
        query = query.filter(User.age <= max_age)
    if min_gender_probability is not None:
        query = query.filter(User.gender_probability >= min_gender_probability)
    if min_country_probability is not None:
        query = query.filter(User.country_probability >= min_country_probability)

    SORTABLE_FIELDS = {"age", "created_at", "gender_probability"}

    if sort_by:
        if sort_by not in SORTABLE_FIELDS:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Invalid sort_by field: '{sort_by}'. Allowed: age, created_at, gender_probability"
            )
        if order not in ("asc", "desc"):
            order = "asc"
        if order == "desc":
            query = query.order_by(getattr(User, sort_by).desc())
        else:
            query = query.order_by(getattr(User, sort_by))

    page = page if page is not None else 1
    limit = min(limit if limit is not None else 10, 50)

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    users = query.all()
    return success_list_response(
        status_code=status.HTTP_200_OK,
        data=[_serialize_user(user) for user in users],
        count=len(users),
        page=page,
        limit=limit
    )


async def search_users_by_query(
    db: Session,
    q: str,
    limit: int = None,
    page: int = None,
) -> dict:
    if not q or not q.strip():
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Missing or empty query"
        )

    filters = parse_query(q)
    if filters is None:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Unable to interpret query"
        )

    return await get_all_users(
        db=db,
        gender=filters.get("gender"),
        age_group=filters.get("age_group"),
        country_id=filters.get("country_id"),
        min_age=filters.get("min_age"),
        max_age=filters.get("max_age"),
        limit=limit,
        page=page,
    )
