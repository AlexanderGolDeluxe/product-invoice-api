from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import NonNegativeInt, NonNegativeFloat

from app.config import API_PREFIX
from app.configuration.db_helper import db_helper
from app.internal.crud.invoice import (
    generate_invoice, get_invoices, get_pretty_invoice
)
from app.internal.routes.auth import get_current_auth_user
from app.internal.schemas import (
    InvoiceCreate, InvoiceSchema, InvoicesSchema, UserSchema
)
from app.utils.prettify_invoice import ticket_response_example

router = APIRouter(prefix=API_PREFIX + "/invoice", tags=["invoice"])


@router.post("/create", response_model=InvoiceSchema, status_code=201)
async def create_invoice(
        invoice_in: InvoiceCreate,
        user: UserSchema = Depends(get_current_auth_user),
        session: AsyncSession = Depends(
            db_helper.scoped_session_dependency)):

    return await generate_invoice(session, invoice_in, user)


@router.get("/retrieve", response_model=InvoicesSchema)
async def get_owned_invoices(
        from_created_at: str = None,
        to_created_at: str = None,
        max_total: NonNegativeFloat = None,
        min_total: NonNegativeFloat = None,
        payment_type: Literal["cash", "cashless"] = None,
        page: NonNegativeInt = 0,
        limit: NonNegativeInt = None,
        user: UserSchema = Depends(get_current_auth_user),
        session: AsyncSession = Depends(
            db_helper.scoped_session_dependency)):

    return await get_invoices(
        session,
        user.id,
        from_created_at,
        to_created_at,
        max_total,
        min_total,
        payment_type,
        page,
        limit)


@router.get(
        "/{invoice_id}",
        response_class=PlainTextResponse,
        responses={"200": ticket_response_example})
async def get_represented_invoice(
        invoice_id: Annotated[int, Path(ge=1)],
        session: AsyncSession = Depends(
            db_helper.scoped_session_dependency)):

    return await get_pretty_invoice(session, invoice_id)
