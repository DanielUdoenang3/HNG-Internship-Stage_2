from fastapi import APIRouter
from app.api.controller.profile import (
    create_user_controller,
    get_user_controller,
    get_all_users_controller,
    delete_user_controller,
)

router = APIRouter(prefix="/api", tags=["Profiles"])

router.add_api_route(
    "/profiles",
    endpoint=create_user_controller,
    methods=["POST"],
    summary="Create a user profile",
)

router.add_api_route(
    "/profiles",
    endpoint=get_all_users_controller,
    methods=["GET"],
    summary="Get all profiles with optional filters",
)

router.add_api_route(
    "/profiles/{id}",
    endpoint=get_user_controller,
    methods=["GET"],
    summary="Get a single profile by ID",
)

router.add_api_route(
    "/profiles/{id}",
    endpoint=delete_user_controller,
    methods=["DELETE"],
    summary="Delete a profile by ID",
)
