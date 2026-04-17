from app.models.base import User
from app.schema.profile import UserProfile
from sqlalchemy.orm import Session
from app.utils.custom_response import (
    error_response,
    success_response,
    success_list_response,
    gateway_error_response,
)
from fastapi import status
import httpx
from app.utils.settings import settings


def _classify_age_group(age: int) -> str:
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    return "senior"


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "gender": user.gender,
        "gender_probability": user.gender_probability,
        "sample_size": user.sample_size,
        "age": user.age,
        "age_group": user.age_group,
        "country_id": user.country_id,
        "country_probability": user.country_probability,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_user_list(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "age_group": user.age_group,
        "country_id": user.country_id,
    }


async def create_user(data: UserProfile, db: Session):
    # Check for duplicate
    existing = db.query(User).filter(User.name == data.name.strip().lower()).first()
    if existing:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Profile already exists",
            data=_serialize_user(existing),
        )

    params = {"name": data.name.strip().lower()}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            genderize_response = await client.get(settings.GENDERIZE_URL, params=params)
            agify_response = await client.get(settings.AGIFY_URL, params=params)
            nationalize_response = await client.get(settings.NATIONALIZE_URL, params=params)
        except httpx.HTTPError:
            return error_response(
                status_code=status.HTTP_502_BAD_GATEWAY,
                message="Upstream or server failure",
            )

    if genderize_response.status_code != 200:
        return gateway_error_response("Genderize")
    if agify_response.status_code != 200:
        return gateway_error_response("Agify")
    if nationalize_response.status_code != 200:
        return gateway_error_response("Nationalize")

    genderize_payload = genderize_response.json()
    agify_payload = agify_response.json()
    nationalize_payload = nationalize_response.json()

    # Edge case validation
    gender = genderize_payload.get("gender")
    sample_size = genderize_payload.get("count")
    if not gender or not sample_size:
        return gateway_error_response("Genderize")

    age = agify_payload.get("age")
    if age is None:
        return gateway_error_response("Agify")

    countries = nationalize_payload.get("country")
    if not countries:
        return gateway_error_response("Nationalize")

    gender_probability = genderize_payload.get("probability", 0.0)
    age_group = _classify_age_group(age)

    # Pick country with highest probability
    top_country = max(countries, key=lambda c: c.get("probability", 0))
    country_id = top_country.get("country_id")
    country_probability = top_country.get("probability", 0.0)

    user = User(
        name=data.name.strip().lower(),
        gender=gender,
        gender_probability=gender_probability,
        sample_size=sample_size,
        age=age,
        age_group=age_group,
        country_id=country_id,
        country_probability=country_probability,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        data=_serialize_user(user),
    )


async def get_user(user_id: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Profile not found",
        )
    return success_response(status_code=status.HTTP_200_OK, data=_serialize_user(user))


async def get_all_users(db: Session, gender: str = None, country_id: str = None, age_group: str = None):
    query = db.query(User)

    if gender:
        query = query.filter(User.gender == gender.lower())
    if country_id:
        query = query.filter(User.country_id == country_id.upper())
    if age_group:
        query = query.filter(User.age_group == age_group.lower())

    users = query.all()
    return success_list_response(
        status_code=status.HTTP_200_OK,
        data=[_serialize_user_list(u) for u in users],
        count=len(users),
    )


async def delete_user(user_id: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Profile not found",
        )
    db.delete(user)
    db.commit()
    return None  # 204 No Content
