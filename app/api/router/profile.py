from fastapi import APIRouter
from app.api.controller.profile import (
    get_all_users_controller,
    seed_users_controller,
    search_users_controller,
)

router = APIRouter(prefix="/api", tags=["Profiles"])

router.add_api_route(
    "/profiles",
    endpoint=get_all_users_controller,
    methods=["GET"],
    summary="Get all profiles with optional filters",
)

# router.add_api_route(
#     "/profiles/search",
#     endpoint=get_all_users_controller,
#     methods=["GET"],
#     summary="Get all profiles with optional filters",
# )

router.add_api_route(
    "/profiles/seed",
    endpoint=seed_users_controller,
    methods=["POST"],
    summary="Seed profiles from seed_profiles.json",
)

router.add_api_route(
    "/profiles/search",
    endpoint=search_users_controller,
    methods=["GET"],
    summary="Natural language search — e.g. ?q=young males from nigeria",
)
