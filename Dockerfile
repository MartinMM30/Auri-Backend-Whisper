FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libasound2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Railway asigna PORT dinámico
EXPOSE 8000

# Ejecutamos main.py que lee PORT correctamente
CMD ["python", "main.py"]
