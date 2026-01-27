# PYTHON CHALLENGE - 001 FastAPI
#USING FASTAPI TO CREATE A LOGIN API
from fastapi import FastAPI
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

app = FastAPI()


@app.post("/login")
async def create_login(request: LoginRequest):
    return request.username + request.password