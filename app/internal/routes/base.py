from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(include_in_schema=False)


@router.get("/", status_code=307)
async def index():
    return RedirectResponse("/docs")
