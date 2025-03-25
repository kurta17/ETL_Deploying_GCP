FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Cloud Run uses the environment variable PORT
ENV PORT 8080

# Use Functions Framework to serve the function
CMD exec functions-framework --target=etl_pipeline --port=$PORT
