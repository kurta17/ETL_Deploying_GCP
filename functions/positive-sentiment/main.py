import base64
import json
import os
import logging
import requests
from flask import Flask, request
from google.cloud import language_v1
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

# Initialize Natural Language client
language_client = language_v1.LanguageServiceClient()

# Get project ID
project_id = os.environ.get('PROJECT_ID', os.environ.get('GOOGLE_CLOUD_PROJECT'))
slack_channel = os.environ.get('SLACK_CHANNEL', '#followup')  # Channel for positive feedback

def get_slack_token():
    """Retrieve Slack token from Secret Manager."""
    name = f"projects/{project_id}/secrets/SLACK_TOKEN/versions/latest"
    response = secret_client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def analyze_sentiment(text):
    """Analyzes text sentiment using Google Natural Language API."""
    document = language_v1.Document(
        content=text, type_=language_v1.Document.Type.PLAIN_TEXT
    )
    sentiment = language_client.analyze_sentiment(
        request={"document": document}
    ).document_sentiment
    
    # Determine sentiment category
    if sentiment.score >= 0.2:
        return "positive", sentiment.score
    elif sentiment.score <= -0.2:
        return "negative", sentiment.score
    else:
        return "neutral", sentiment.score

def send_slack_alert(message, sentiment, score, user_id):
    """Sends an alert to Slack for positive sentiment."""
    token = get_slack_token()
    
    # Only process positive sentiment
    if sentiment == "positive":
        emoji = ":smile:"
        color = "#36a64f"  # Green
        
        # Prepare Slack message payload
        payload = {
            "channel": slack_channel,
            "attachments": [
                {
                    "color": color,
                    "pretext": f"New positive feedback received! {emoji}",
                    "author_name": f"User: {user_id}",
                    "title": f"Sentiment Score: {score:.2f}",
                    "text": message
                }
            ]
        }
        
        # Send to Slack
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload
        )
        return response.json()
    return None

@app.route('/', methods=['POST'])
def process_pubsub_message():
    """Process Pub/Sub messages and analyze sentiment."""
    envelope = request.get_json()
    
    # Extract Pub/Sub message
    if not envelope or 'message' not in envelope:
        logger.error("No Pub/Sub message received")
        return 'No Pub/Sub message received', 400
    
    # Decode the message data
    pubsub_message = envelope['message']
    logger.info(f"Received Pub/Sub message: {pubsub_message}")
    
    if not pubsub_message.get('data'):
        logger.error("No data in message")
        return 'No data in message', 400
    
    try:
        # Decode and parse the message
        message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
        feedback = json.loads(message_data)
        
        # Validate required fields
        if 'message' not in feedback or 'user_id' not in feedback:
            logger.error("Missing required fields in message")
            return 'Missing required fields in feedback', 400
        
        # Analyze sentiment
        sentiment, score = analyze_sentiment(feedback['message'])
        
        # Log the analysis result
        logger.info(f"Feedback analyzed - User: {feedback['user_id']}, Sentiment: {sentiment}, Score: {score}")
        
        # Send Slack alert only for positive sentiment
        if sentiment == "positive":
            try:
                slack_response = send_slack_alert(
                    message=feedback['message'],
                    sentiment=sentiment,
                    score=score,
                    user_id=feedback['user_id']
                )
                if slack_response and not slack_response.get('ok'):
                    logger.warning(f"Slack API error: {slack_response.get('error')}")
                else:
                    logger.info(f"Alert sent to Slack {slack_channel} for positive feedback")
            except Exception as slack_err:
                logger.error(f"Error sending Slack alert: {slack_err}")
                # Continue execution even if Slack alert fails
        
        return 'Message processed successfully', 200
    
    except json.JSONDecodeError as json_err:
        logger.error(f"Invalid JSON in message: {json_err}")
        return f'Error: Invalid JSON format: {str(json_err)}', 400
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return f'Error: {str(e)}', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
