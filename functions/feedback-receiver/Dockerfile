FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
