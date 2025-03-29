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

# Feedback Sentiment Analysis System on GCP

This project implements a feedback sentiment analysis system on Google Cloud Platform that:
1. Receives user feedback via HTTP endpoint
2. Analyzes sentiment using Google Natural Language API
3. Routes feedback to appropriate Slack channels based on sentiment

## Architecture

- **HTTP Receiver Function**: Accepts HTTP requests with feedback and publishes to Pub/Sub
- **Positive Sentiment Function**: Processes positive feedback and sends alerts to #followup Slack channel
- **Negative Sentiment Function**: Processes negative feedback and sends alerts to #support Slack channel
- **Pub/Sub Topic**: Routes messages between functions
- **Optional BigQuery Integration**: Stores all feedback messages for analysis

## Prerequisites

- Google Cloud account with billing enabled
- Google Cloud SDK installed
- Terraform (optional, for infrastructure as code)
- Slack workspace with a bot integration and token

## Deployment

### 1. Set up Slack Token in Secret Manager

```bash
# Create a secret for the Slack token
echo -n "xoxb-your-slack-token" | gcloud secrets create SLACK_TOKEN --data-file=-

# Grant access to the service account
gcloud secrets add-iam-policy-binding SLACK_TOKEN \
    --member="serviceAccount:sentiment-analyzer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Deploy using script

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### 3. Using Terraform (Alternative)

```bash
cd terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" \
                -var="positive_function_url=POSITIVE_FUNCTION_URL" \
                -var="negative_function_url=NEGATIVE_FUNCTION_URL" \
                -var="pubsub_service_account=SERVICE_ACCOUNT_EMAIL" \
                -var="create_bigquery=true"
```

## Testing with Postman

Send POST requests to the HTTP Receiver function URL with different sentiment messages:

### 1. Positive Sentiment

```json
{
  "user_id": "happy.user@example.com",
  "message": "I absolutely love this service! It has been incredibly helpful and the customer support is amazing."
}
```

### 2. Negative Sentiment

```json
{
  "user_id": "unhappy.user@example.com",
  "message": "This is terrible. I've been trying for hours and nothing works. Very disappointed with the service."
}
```

### 3. Neutral Sentiment

```json
{
  "user_id": "neutral.user@example.com",
  "message": "I submitted the form as requested. Please process my application when you have time."
}
```

## Flow Monitoring

1. Check Cloud Run Function logs for execution details
2. Verify Pub/Sub message delivery in the Cloud Console
3. Confirm Slack message delivery to the appropriate channels (#followup or #support)
4. If BigQuery is enabled, query the table to see all recorded feedback
