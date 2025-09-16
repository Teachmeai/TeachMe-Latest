from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from core.config import config

def setup_cors(app: FastAPI):
    app.add_middleware(
    CORSMiddleware,
    allow_origins=config.app.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])
        