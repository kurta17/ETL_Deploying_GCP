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

# ETL Pipeline on Google Cloud Platform

This project implements an ETL pipeline on Google Cloud Platform using Cloud Functions and Cloud Build for deployment.

## Deployment with Cloud Build (One-by-One)

To deploy the ETL pipeline components individually with Cloud Build:

1. Make sure you have the Google Cloud SDK installed and configured
2. Enable necessary APIs:
   ```
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

3. Deploy the extract function independently:
   ```
   cd extract_function
   gcloud builds submit --config=cloudbuild.yaml
   ```

4. Deploy the load function independently:
   ```
   cd load_function
   gcloud builds submit --config=cloudbuild.yaml
   ```

This approach allows you to deploy and update each part of the ETL pipeline separately.

## Permissions

Ensure the Cloud Build service account has the following permissions:
- Cloud Functions Developer
- Service Account User
- Storage Admin (for the target buckets)

You can grant these permissions using:
```
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/storage.admin"
```
