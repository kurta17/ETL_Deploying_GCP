#!/bin/bash

# Set your project ID here
PROJECT_ID=$(gcloud config get-value project)
echo "Setting up infrastructure for project: $PROJECT_ID"

# Create Pub/Sub topic
echo "Creating feedback-topic..."
gcloud pubsub topics create feedback-topic

# Create subscriptions
echo "Creating subscriptions..."
gcloud pubsub subscriptions create positive-sub --topic=feedback-topic
gcloud pubsub subscriptions create negative-sub --topic=feedback-topic

# Create Secret Manager secret for Slack token
echo "Creating Secret Manager secret for Slack token..."
read -sp "Enter your Slack token: " SLACK_TOKEN
echo 

echo -n "$SLACK_TOKEN" | gcloud secrets create SLACK_TOKEN --data-file=-

# Give permissions to Secret Manager
echo "Setting up permissions..."
# Replace with your service account or use the default Cloud Run service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="Cloud Run Service Agent" --format="value(email)")
gcloud secrets add-iam-policy-binding SLACK_TOKEN \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

echo "Infrastructure setup complete!"
