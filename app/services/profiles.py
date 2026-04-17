from app.models.base import User
from app.schema.profile import UserProfile
from sqlalchemy.orm import Session
from app.utils.custom_response import error_response, success_response, gateway_error_response
from fastapi import status
import httpx
from app.utils.settings import settings


async def create_user(data: UserProfile, db: Session) -> User:
    genderize_url = settings.GENDERIZE_URL
    agify_url = settings.AGIFY_URL
    nationalize_url = settings.NATIONALIZE_URL
    params = {"name": data.name}

    if not data:
        return error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Missing or empty name"
        )
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            genderize_response = await client.get(genderize_url, params=params)
            if genderize_response.status_code != 200:
                return gateway_error_response("Genderize")

            agify_response = await client.get(agify_url, params=params)
            if agify_response.status_code != 200:
                return gateway_error_response("Agify")

            nationalize_response = await client.get(nationalize_url, params=params)
            if nationalize_response.status_code != 200:
                return gateway_error_response("Nationalize")

        except httpx.HTTPError:
            return error_response(
                status_code=status.HTTP_502_BAD_GATEWAY,
                message="Upstream or server failure"
            )