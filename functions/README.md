# Sentiment Analysis Pipeline

This project creates a sentiment analysis pipeline using Google Cloud services. It processes user feedback, analyzes sentiment, and sends alerts to appropriate Slack channels.

## Infrastructure Setup

### 1. Pub/Sub Setup

Create a topic and two subscriptions:

```bash
# Create the feedback topic
gcloud pubsub topics create feedback-topic

# Create subscription for positive sentiment analysis
gcloud pubsub subscriptions create positive-sub \
  --topic=feedback-topic \
  --push-endpoint=[POSITIVE_FUNCTION_URL] \
  --ack-deadline=60

# Create subscription for negative sentiment analysis
gcloud pubsub subscriptions create negative-sub \
  --topic=feedback-topic \
  --push-endpoint=[NEGATIVE_FUNCTION_URL] \
  --ack-deadline=60
```

Optional: To create a subscription that forwards data to BigQuery:

```bash
# Create a BigQuery subscription
gcloud pubsub subscriptions create bigquery-sub \
  --topic=feedback-topic \
  --bigquery-table=PROJECT_ID:DATASET.TABLE \
  --write-metadata
```

BigQuery table schema:
```json
[
  {"name": "user_id", "type": "STRING"},
  {"name": "message", "type": "STRING"}
]
```

### 2. Slack Token Setup

Store your Slack API token in Secret Manager:

```bash
echo -n "xoxb-your-token-here" | \
  gcloud secrets create SLACK_TOKEN \
  --data-file=- \
  --replication-policy="automatic"
```

### 3. Deploy Cloud Functions

Each function is located in its own directory with a `main.py` file.

#### HTTP Receiver Function

```bash
gcloud functions deploy http-receiver \
  --runtime=python310 \
  --entry-point=receive_message \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=PUBSUB_TOPIC=feedback-topic
```

#### Positive Sentiment Function

```bash
gcloud functions deploy positive-sentiment \
  --runtime=python310 \
  --entry-point=process_pubsub_message \
  --trigger-topic=positive-sub \
  --set-env-vars=SLACK_CHANNEL=#followup
```

#### Negative Sentiment Function

```bash
gcloud functions deploy negative-sentiment \
  --runtime=python310 \
  --entry-point=process_pubsub_message \
  --trigger-topic=negative-sub \
  --set-env-vars=SLACK_CHANNEL=#support
```

## Testing the Pipeline

Using Postman or curl, send a POST request to the HTTP receiver function:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user@example.com", "message": "I really love this product!"}' \
  https://YOUR_FUNCTION_URL
```

Test with different message types:
- Positive: "I really love this product! It's amazing!"
- Neutral: "The product works as expected."
- Negative: "This product is terrible and doesn't work at all."

## Requirements

- `requirements.txt` for each function should include:
  - Flask
  - google-cloud-pubsub
  - google-cloud-language
  - google-cloud-secretmanager
  - requests
