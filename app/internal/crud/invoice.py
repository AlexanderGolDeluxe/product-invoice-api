import math
from typing import Literal

from fastapi import HTTPException, status
from loguru import logger
from pydantic import NonNegativeFloat, NonNegativeInt
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, load_only

from app.internal.models import (
    Invoice, InvoiceProductAssociation, Payment, Product, User
)
from app.internal.schemas import (
    InvoiceCreate,
    InvoiceProductAssociationCreate,
    InvoiceProductAssociationSchema,
    InvoiceSchema,
    InvoicesSchema,
    PaymentSchema,
    UserSchema
)
from app.utils.prettify_invoice import invoice_to_ticket_format
from app.utils.work_with_dates import parse_like_date


@logger.catch(reraise=True)
async def generate_invoice_product_association_objects(
        session: AsyncSession,
        products_in: list[InvoiceProductAssociationCreate]
    ):
    """
    Collects invoice-product association objects,
    using existing products or creating new ones
    """
    stmt = select(Product).where(or_(
        (Product.name == product.name) &
        (Product.price == product.price)
        for product in products_in
    ))
    existing_products = (await session.scalars(stmt)).all()
    product_objects = {
        (product.name, product.price): product
        for product in existing_products
    }
    invoice_product_association_objects = list()
    for product_in in products_in:
        product_object = product_objects.get(
            (product_in.name, product_in.price),
            Product(
                name=product_in.name,
                price=product_in.price,
                description=product_in.description)
        )
        invoice_product_association_objects.append(
            InvoiceProductAssociation(
                product=product_object,
                quantity=product_in.quantity,
                unit_price=product_in.price))

    return invoice_product_association_objects


@logger.catch(reraise=True)
async def generate_invoice(
        session: AsyncSession,
        invoice_in: InvoiceCreate,
        created_by: UserSchema
    ):
    """
    Validates invoice data from user,
    calculates remaining fields and generates the invoice,
    after that saving it in database
    """
    created_invoice = dict(
        created_by=created_by,
        total=sum(
            product.price * product.quantity
            for product in invoice_in.products)
    )
    created_invoice["rest"] = (
        invoice_in.payment.amount - created_invoice["total"]
    )
    if created_invoice["rest"] < 0:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid invoice data. "
                f"Payment amount ({invoice_in.payment.amount}) canʼt be "
                f"less than total ({created_invoice['total']})"))

    invoice = Invoice(
        total=created_invoice["total"],
        rest=created_invoice["rest"],
        created_by=created_by.id)

    # Insert payment
    invoice.payment = Payment(**invoice_in.payment.model_dump())

    # Insert product with invoice items
    invoice.products.extend(
        await generate_invoice_product_association_objects(
            session, invoice_in.products))

    session.add(invoice)
    await session.commit()

    return InvoiceSchema(
        id=invoice.id,
        products=[
            InvoiceProductAssociationSchema(
                name=invoice_product_association.product.name,
                price=invoice_product_association.product.price,
                description=(
                    invoice_product_association.product.description
                ),
                quantity=invoice_product_association.quantity,
                unit_price=invoice_product_association.unit_price,
                total=invoice_product_association.total
            )
            for invoice_product_association in invoice.products
        ],
        payment=PaymentSchema(
            id=invoice.payment.id,
            type=invoice.payment.type,
            amount=invoice.payment.amount
        ),
        created_at=invoice.created_at,
        **created_invoice)


@logger.catch(reraise=True)
async def select_invoices(session: AsyncSession, where_clauses: list):
    """Executes query to search for invoices using received filters"""
    stmt = (
        select(Invoice)
        .options(
            load_only(Invoice.total, Invoice.rest, Invoice.created_at)
        )
        .join(Invoice.payment)
        .options(
            contains_eager(Invoice.payment)
            .options(load_only(Payment.type, Payment.amount))
        )
        .options(
            joinedload(Invoice.user_owner)
            .options(load_only(User.name, User.login))
        )
        .join(Invoice.products)
        .options(
            contains_eager(Invoice.products)
            .load_only(
                InvoiceProductAssociation.quantity,
                InvoiceProductAssociation.unit_price,
                InvoiceProductAssociation.total
            )
            .joinedload(InvoiceProductAssociation.product)
        )
        .where(*where_clauses)
        .order_by(desc(Invoice.created_at))
    )
    result = (await session.scalars(stmt)).unique().all()
    # Preparing to pydantic InvoiceSchema model
    for row in result:
        row.created_by = row.user_owner
        for product in row.products:
            product.name = product.product.name
            product.price = product.product.price
            product.description = product.product.description

    return result


@logger.catch(reraise=True)
async def get_invoices(
        session: AsyncSession,
        owner_id: int,
        from_created_at: str | None,
        to_created_at: str | None,
        max_total: NonNegativeFloat | None,
        min_total: NonNegativeFloat | None,
        payment_type: Literal["cash", "cashless"] | None,
        page: NonNegativeInt,
        limit: NonNegativeInt | None
    ):
    """
    Converts filters from user into where clauses, sends them to query.
    Generates pagination data and append it to response
    """
    where_clauses = [Invoice.created_by == owner_id]
    if from_created_at is not None:
        where_clauses.append(
            Invoice.created_at >= parse_like_date(from_created_at))

    if to_created_at is not None:
        where_clauses.append(
            Invoice.created_at <= parse_like_date(to_created_at))

    if max_total is not None:
        where_clauses.append(Invoice.total <= max_total)

    if min_total is not None:
        where_clauses.append(Invoice.total >= min_total)

    if payment_type is not None:
        where_clauses.append(Payment.type == payment_type)

    response = InvoicesSchema.model_validate(
        dict(
            limit=limit,
            invoices=await select_invoices(session, where_clauses)
        ),
        from_attributes=True
    )
    if limit:
        response.current_page = page
        response.last_page = (
            math.ceil(len(response.invoices) / limit) - 1
        )
        response.invoices = (
            response.invoices[page * limit:(page + 1) * limit])

    return response


@logger.catch(reraise=True)
async def get_pretty_invoice(session: AsyncSession, invoice_id: int):
    """
    Finds for invoice by specified ID
    and returns it in `plain/text` format
    """
    invoices = await select_invoices(session, [Invoice.id == invoice_id])
    if not invoices:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID = {invoice_id} not found")

    return invoice_to_ticket_format(invoices[0])
