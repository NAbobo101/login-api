# PYTHON CHALLENGE - 001 FastAPI
#USING FASTAPI TO CREATE A LOGIN API

from fastapi import FastAPI
import uvicorn
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the Login API"}

async def app(scope, receive, send):
    assert scope['type'] == 'http'

    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
    })
    await send({
        'type': 'http.response.body',
        'body': b'Hello, World!',
    })