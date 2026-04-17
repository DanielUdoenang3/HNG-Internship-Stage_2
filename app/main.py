from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
# from app.api.router.genderize import router


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

@app.get("/")
def read_root():
    return {"message": "Welcome to Daniel Udoenang's HNG-Internship Stage 1 Genderize, Agify, and Nationalize API!"}