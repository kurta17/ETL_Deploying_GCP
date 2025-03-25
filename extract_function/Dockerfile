FROM python:3.9-slim

WORKDIR /app

# Copy function code and dependencies
COPY main.py .
COPY requirements.txt .
COPY credintal.json .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cloud Functions uses the function name as the entrypoint
ENV FUNCTION_NAME=extract_to_gcs
ENV FUNCTION_SIGNATURE_TYPE=http

# Run the web service on container startup
CMD functions-framework --target=${FUNCTION_NAME} --signature-type=${FUNCTION_SIGNATURE_TYPE}
