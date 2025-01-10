from fastapi import FastAPI

from app.config import DEBUG_MODE
from app.configuration.server import Server, lifespan


def create_app(_=None):
    app = FastAPI(debug=DEBUG_MODE, lifespan=lifespan)

    return Server(app).get_app()
