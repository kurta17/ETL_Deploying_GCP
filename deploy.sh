#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"

echo "Deploying ETL Sentiment Analysis on GCP Project: $PROJECT_ID in $REGION"

# Create service account if it doesn't exist
echo "Creating service account for Cloud Run..."
SA_NAME="sentiment-analyzer-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
    --display-name="Sentiment Analyzer Service Account" \
    --description="Used by Cloud Run functions for sentiment analysis" \
    || echo "Service account already exists"

# Grant necessary permissions
echo "Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/languageservice.user"

# Deploy the HTTP receiver function
echo "Deploying HTTP receiver function..."
gcloud functions deploy http-receiver \
    --gen2 \
    --runtime=python310 \
    --region=$REGION \
    --source=./functions/http-receiver \
    --entry-point=receive_feedback \
    --trigger-http \
    --allow-unauthenticated \
    --service-account=$SA_EMAIL \
    --set-env-vars="PUBSUB_TOPIC=feedback-topic,PROJECT_ID=$PROJECT_ID"

HTTP_URL=$(gcloud functions describe http-receiver --region=$REGION --gen2 --format="value(serviceConfig.uri)")
echo "HTTP Receiver function deployed at: $HTTP_URL"

# Deploy the positive sentiment analyzer function
echo "Deploying positive sentiment analyzer function..."
gcloud functions deploy positive-sentiment \
    --gen2 \
    --runtime=python310 \
    --region=$REGION \
    --source=./functions/positive-sentiment \
    --entry-point=process_pubsub_message \
    --set-env-vars="SLACK_CHANNEL=#followup,PROJECT_ID=$PROJECT_ID" \
    --trigger-topic=feedback-topic \
    --service-account=$SA_EMAIL

# Deploy the negative sentiment analyzer function
echo "Deploying negative sentiment analyzer function..."
gcloud functions deploy negative-sentiment \
    --gen2 \
    --runtime=python310 \
    --region=$REGION \
    --source=./functions/negative-sentiment \
    --set-env-vars="SLACK_CHANNEL=#support,PROJECT_ID=$PROJECT_ID" \
    --entry-point=process_pubsub_message \
    --trigger-topic=feedback-topic \
    --service-account=$SA_EMAIL

echo "All functions deployed successfully!"
echo "You can now send test messages to: $HTTP_URL"
