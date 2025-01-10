import textwrap
from decimal import Decimal

from loguru import logger

from app.config import INVOICE_TICKET_MAX_WIDTH
from app.internal.schemas import (
    InvoiceProductAssociationSchema, InvoiceSchema)

ticket_example = (
"""      ФОП Джонсонюк Борис
================================
3.00 x 298 870.00
Mavic 3T              896 610.00
--------------------------------
20.00 х 31 000.00
Дрон FPV з акумулятором
6S чорний             620 000.00
================================
СУМА                1 516 610.00
Картка              1 516 610.00
Решта                       0.00
================================
       14.08.2023 14:42:00
       Дякуємо за покупку!"""
)
ticket_response_example = {
    "description": "Successfully generated Invoice",
    "content": {"text/plain": {"example": ticket_example}}
}


@logger.catch(reraise=True)
def add_thousands_separator(number: Decimal | float | int):
    """Formats float numbers into string with spaces between thousands"""
    return format(number, ",.2f").replace(",", " ")


@logger.catch(reraise=True)
def wrap_head_text(text: str, line_width: int, centered_line_width: int):
    """Centers header text within a block of fixed-length lines"""
    wrapped_text = (
        line.center(centered_line_width)
        for line in textwrap.wrap(text, line_width))

    return "\n".join(wrapped_text)


@logger.catch(reraise=True)
def add_space_between(
        text: str, number: Decimal | float | int, line_max_width: int
    ):
    """
    Separates text and number to different edges of fixed-length lines
    """
    wrapped_text = textwrap.wrap(text, line_max_width - 7)
    last_line_length = len(wrapped_text[-1])
    formatted_number = add_thousands_separator(number)
    if last_line_length + len(formatted_number) + 10 <= line_max_width:
        wrapped_text[-1] += (
            formatted_number.rjust(line_max_width - last_line_length))
    else:
        wrapped_text.append(formatted_number.rjust(line_max_width))

    return "\n".join(wrapped_text)


@logger.catch(reraise=True)
def products_text_formatting(
        products: list[InvoiceProductAssociationSchema],
        line_max_width: int
    ):
    """Formats items of invoice by listing them using a delimiter"""
    pruducts_separator = "\n" + "-" * line_max_width + "\n"
    products_text_formatted = pruducts_separator.join(
        add_thousands_separator(product.quantity) + " x " +
        add_thousands_separator(product.unit_price) + "\n" +
        add_space_between(product.name, product.total, line_max_width)
        for product in products)

    return products_text_formatted


@logger.catch(reraise=True)
def invoice_to_ticket_format(invoice: InvoiceSchema):
    """Generates an invoice in `plain/text` ticket format"""
    ticket_max_width = INVOICE_TICKET_MAX_WIDTH
    blocks_separator = "=" * ticket_max_width
    payment_type = (
        "Готівка" if invoice.payment.type == "cash" else "Картка"
    )
    ticket = "\n".join((
        wrap_head_text(
            text=invoice.created_by.name.capitalize(),
            line_width=ticket_max_width - 8,
            centered_line_width=ticket_max_width
        ),
        blocks_separator,
        products_text_formatting(invoice.products, ticket_max_width),
        blocks_separator,
        add_space_between("СУМА", invoice.total, ticket_max_width),
        add_space_between(
            payment_type, invoice.payment.amount, ticket_max_width
        ),
        add_space_between("Решта", invoice.rest, ticket_max_width),
        blocks_separator,
        invoice.created_at.strftime("%d.%m.%Y %H:%M:%S").center(33),
        "Дякуємо за покупку!".center(33)
    ))

    return ticket
