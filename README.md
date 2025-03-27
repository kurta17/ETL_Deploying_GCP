# Books ETL Pipeline on GCP

This project implements an ETL (Extract, Transform, Load) pipeline that:
1. Scrapes book data from [Books to Scrape](https://books.toscrape.com/)
2. Transforms the data into a structured format
3. Loads data to Google Cloud Storage (GCS)
4. Loads data to BigQuery for analysis

The pipeline is deployed as a Cloud Run function and is automatically triggered on a schedule using Cloud Scheduler.

## Architecture

```
Web Scraping → Data Transformation → GCS Storage → BigQuery
        ↑                                              
Cloud Scheduler → Cloud Run Function                   
```

## Requirements

- Google Cloud Platform account
- The following APIs enabled:
  - Cloud Run
  - Cloud Storage
  - BigQuery
  - Cloud Scheduler
- Service account with appropriate permissions

## Setup Instructions

### 1. GCP Resources Setup

```bash
# Create GCS bucket
gsutil mb -p [PROJECT_ID] -l [LOCATION] gs://[BUCKET_NAME]

# Create BigQuery dataset
bq mk --dataset [PROJECT_ID]:[DATASET_ID]

# Create BigQuery table
bq mk --table [PROJECT_ID]:[DATASET_ID].[TABLE_ID] title:STRING,price:FLOAT,rating:STRING,scraped_date:DATE
```

### 2. GitHub Repository Setup

1. Fork this repository
2. Add the following secrets to your GitHub repository:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: The JSON key of your service account
   - `GCS_BUCKET_NAME`: Name of your GCS bucket
   - `BQ_DATASET_ID`: BigQuery dataset ID
   - `BQ_TABLE_ID`: BigQuery table ID

### 3. Deployment

The CI/CD pipeline will automatically deploy the function when you push to the main branch.

To manually deploy:

```bash
# Build the image
docker build -t gcr.io/[PROJECT_ID]/etl-books-service .

# Push to Container Registry
docker push gcr.io/[PROJECT_ID]/etl-books-service

# Deploy to Cloud Run
gcloud run deploy etl-books-service \
  --image gcr.io/[PROJECT_ID]/etl-books-service \
  --platform managed \
  --region [REGION] \
  --set-env-vars="GCS_BUCKET_NAME=[BUCKET_NAME],BQ_DATASET_ID=[DATASET_ID],BQ_TABLE_ID=[TABLE_ID]"

# Set up Cloud Scheduler
gcloud scheduler jobs create http etl-daily-job \
  --schedule="0 0 * * *" \
  --uri=[CLOUD_RUN_URL] \
  --time-zone="UTC"
```

## Local Development

1. Set up a Python virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables or create a `.env` file
4. Run `python main.py` for testing

## Data Schema

- **title**: Book title (string)
- **price**: Book price in GBP (float)
- **rating**: Book rating (string)
- **scraped_date**: Date the data was scraped (date)

# Pub/Sub Integration Workshop

This project demonstrates how to create a sentiment analysis pipeline using Google Cloud Pub/Sub, Cloud Run, Natural Language API, and Slack integration.

## Architecture

1. **HTTP Endpoint**: Receives feedback messages and publishes them to a Pub/Sub topic.
2. **Sentiment Analyzer**: Triggered by Pub/Sub, analyzes sentiment using the Natural Language API, and sends alerts to Slack for positive/negative feedback.

## Project Structure

```
.
├── infrastructure/
│   └── setup.sh               # Sets up Pub/Sub and Secret Manager
├── functions/
│   ├── feedback-receiver/     # First Cloud Run service (HTTP endpoint)
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── sentiment-analyzer/    # Second Cloud Run service (Pub/Sub triggered)
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── deployment/
│   └── deploy.sh              # Deployment script
├── test/
│   └── test_requests.py       # Test script for sending sample feedback
└── README.md
```

## Setup Instructions

### 1. Create the Infrastructure

```bash
cd infrastructure
chmod +x setup.sh
./setup.sh
```

This script creates:
- A Pub/Sub topic named `feedback-topic`
- Two subscriptions: `positive-sub` and `negative-sub`
- A Secret Manager secret for your Slack token

### 2. Deploy the Cloud Run Services

```bash
cd deployment
chmod +x deploy.sh
./deploy.sh
```

This deploys both Cloud Run services and sets up the Pub/Sub trigger.

### 3. Testing

Update the `FEEDBACK_RECEIVER_URL` in `test/test_requests.py` with your actual Cloud Run URL.

```bash
cd test
python test_requests.py
```

Or use Postman to send requests to your feedback receiver endpoint:

- **Positive Feedback Example:**
```json
{
  "user_id": "user@example.com",
  "message": "I absolutely love this product!"
}
```

- **Neutral Feedback Example:**
```json
{
  "user_id": "user@example.com",
  "message": "The product works fine."
}
```

- **Negative Feedback Example:**
```json
{
  "user_id": "user@example.com",
  "message": "I'm disappointed with the service."
}
```

## Slack Integration

The system will send alerts to your configured Slack channel when positive or negative feedback is received.

- **Positive feedback**: Green message with a smile emoji
- **Negative feedback**: Red message with a disappointed emoji

## Required Google Cloud APIs

- Cloud Run API
- Cloud Build API
- Pub/Sub API
- Secret Manager API
- Natural Language API

## Cleanup

To delete all resources created for this project:

1. Delete the Cloud Run services
2. Delete the Pub/Sub topic and subscriptions
3. Delete the Secret Manager secret

```
gcloud run services delete feedback-receiver --region us-central1
gcloud run services delete sentiment-analyzer --region us-central1
gcloud pubsub topics delete feedback-topic
gcloud secrets delete SLACK_TOKEN
```
