FROM python:latest

WORKDIR /usr/src/product_invoice_api

RUN mkdir ./certs && \
    sh -c "openssl genrsa -out certs/jwt-private.pem 2048 && \
    openssl rsa -in certs/jwt-private.pem -outform PEM -pubout -out certs/jwt-public.pem"

COPY requirements.txt .

ENV TZ="Europe/Kiev" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python3 -m venv .venv
RUN bash -c "source .venv/bin/activate && \
    python3 -m pip install --no-cache-dir -U pip setuptools -r requirements.txt"

COPY . .

CMD [ "bash", "-c", "source .venv/bin/activate && \
    uvicorn app:create_app --reload --host=0.0.0.0 --port=8000" ]
