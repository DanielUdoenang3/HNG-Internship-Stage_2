from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to Daniel Udoenang FastAPI base"}