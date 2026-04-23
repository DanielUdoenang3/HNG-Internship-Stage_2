from typing import Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def success_response(status_code: int, data: Optional[dict] = None, message: Optional[str] = None):
    """Returns a structured response for success responses"""

    response_data = {"status": "success"}

    if message:
        response_data["message"] = message

    response_data["data"] = data or {}

    return JSONResponse(status_code=status_code, content=jsonable_encoder(response_data))


def success_list_response(status_code: int, data: list, count: int, page: int = None, limit: int = None):
    """Returns a structured response for list endpoints"""

    response_data = {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": count,
        "data": data,
    }

    return JSONResponse(status_code=status_code, content=jsonable_encoder(response_data))


def error_response(status_code: int, message: str):
    """Returns a structured response for error responses"""

    response_data = {
        "status": "error",
        "message": message,
    }

    return JSONResponse(status_code=status_code, content=jsonable_encoder(response_data))
