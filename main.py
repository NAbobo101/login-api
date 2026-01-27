# PYTHON CHALLENGE - 001 FastAPI
#USING FASTAPI TO CREATE A LOGIN API

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the Login API"}

