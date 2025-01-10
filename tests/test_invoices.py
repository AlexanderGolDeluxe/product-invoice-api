from datetime import datetime
from pprint import pprint

from httpx import AsyncClient, Headers

from app.config import API_PREFIX

test_invoices = [
    {
        "products": [
            {"name": "Water", "price": 12.3, "quantity": 10},
            {"name": "Ice-cream", "price": 37.7, "quantity": 2}
        ],
        "payment": {"type": "cash", "amount": 200}
    },
    {
        "products": [{"name": "Milk", "price": 25}],
        "payment": {"type": "cash", "amount": 30}
    },
    {
        "products": [
            {"name": "Carrot", "price": 8, "quantity": 5},
            {"name": "Egg", "price": 1.5, "quantity": 4}
        ],
        "payment": {"type": "cash", "amount": 70}
    },
    {
        "products": [
            {"name": "Meat", "price": 170},
            {"name": "Coffee", "price": 90, "quantity": 2}
        ],
        "payment": {"type": "cashless", "amount": 350}
    }
]


async def test_create_invoice(ac: AsyncClient, headers: Headers):
    for invoice in test_invoices:
        response = await ac.post(
            API_PREFIX + "/invoice/create",
            headers=headers,
            json=invoice)

        pprint(response.json())
        assert response.status_code == 201
        assert response.json()["id"]


async def test_decline_invoice_due_to_less_payment_amount(
        ac: AsyncClient, headers: Headers
    ):
    invoice = test_invoices[0].copy()
    invoice["payment"]["amount"] = 100
    response = await ac.post(
        API_PREFIX + "/invoice/create", headers=headers, json=invoice)

    pprint(response.json())
    assert response.status_code == 422


async def test_filtering_invoices(ac: AsyncClient, headers: Headers):
    filters = dict(from_created_at="01.05.2024", min_total=190)
    response = await ac.get(
        API_PREFIX + "/invoice/retrieve", headers=headers, params=filters
    )
    filtered_invoices = response.json()["invoices"]
    assert response.status_code == 200
    assert len(filtered_invoices) == 2
    assert all(
        datetime.strptime(invoice["created_at"], "%Y-%m-%dT%H:%M:%S.%f")
        >= datetime.strptime(filters["from_created_at"], "%d.%m.%Y")
        and invoice["total"] >= filters["min_total"]
        for invoice in filtered_invoices)

    filters = dict(payment_type="cashless", max_total=400)
    response = await ac.get(
        API_PREFIX + "/invoice/retrieve", headers=headers, params=filters
    )
    filtered_invoices = response.json()["invoices"]
    assert response.status_code == 200
    assert len(filtered_invoices) == 1
    assert all(
        invoice["payment"]["type"] == filters["payment_type"] and
        invoice["total"] <= filters["max_total"]
        for invoice in filtered_invoices)

    filters = dict(page=0, limit=3)
    response = await ac.get(
        API_PREFIX + "/invoice/retrieve", headers=headers, params=filters
    )
    filtered_invoices = response.json()
    assert response.status_code == 200
    assert len(filtered_invoices["invoices"]) == 3
    assert filtered_invoices["current_page"] == filters["page"]
    assert filtered_invoices["limit"] == filters["limit"]
    assert filtered_invoices["last_page"] == 1

    filters = dict(page=1, limit=3)
    response = await ac.get(
        API_PREFIX + "/invoice/retrieve", headers=headers, params=filters
    )
    filtered_invoices = response.json()
    pprint(filtered_invoices)
    assert response.status_code == 200
    assert len(filtered_invoices["invoices"]) == 1
    assert filtered_invoices["current_page"] == filters["page"]
    assert filtered_invoices["limit"] == filters["limit"]
    assert filtered_invoices["last_page"] == 1


async def test_invalid_filtering_invoices(
        ac: AsyncClient, headers: Headers
    ):
    response = await ac.get(
        API_PREFIX + "/invoice/retrieve",
        headers=headers,
        params=dict(from_created_at="01/05/2024")
    )
    pprint(response.json())
    assert response.status_code == 422

    response = await ac.get(
        API_PREFIX + "/invoice/retrieve",
        headers=headers,
        params=dict(max_total=-400)
    )
    pprint(response.json())
    assert response.status_code == 422

    response = await ac.get(
        API_PREFIX + "/invoice/retrieve",
        headers=headers,
        params=dict(payment_type="VISA")
    )
    pprint(response.json())
    assert response.status_code == 422


async def test_public_retrieve_invoice_in_text_format(ac: AsyncClient):
    invoice_id = 4
    response = await ac.get(API_PREFIX + f"/invoice/{invoice_id}")
    pprint("\n" + response.text)
    assert response.status_code == 200


async def test_public_invoice_not_found(ac: AsyncClient):
    invoice_id = 5
    response = await ac.get(API_PREFIX + f"/invoice/{invoice_id}")
    pprint(response.json())
    assert response.status_code == 404
