FROM python:3.10-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc libsqlite3-dev curl && \
    rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements y luego instalar
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache

EXPOSE 8080