from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.router.profile import router


class AlwaysCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AlwaysCORSMiddleware)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        loc = error.get("loc", ())
        # Missing/empty body field
        if error.get("type") in ("missing", "value_error") and "name" in loc:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing or empty parameter"},
            )
    # Invalid query param types (e.g. min_age=abc)
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid query parameters"},
    )

app.include_router(router)

@app.get("/")
def read_root():
    return {
        "message": "HNG Internship Stage 2 — Demographic Profiles API",
        "description": "Query, filter, sort, and search demographic profiles using structured filters or plain English.",
        "endpoints": {
            "list": "GET /api/profiles",
            "search": "GET /api/profiles/search?q=young males from nigeria",
            "seed": "POST /api/profiles/seed",
        },
        "docs": "/docs",
    }