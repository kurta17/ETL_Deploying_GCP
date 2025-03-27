import base64
import json
import os
import requests
from flask import Flask, request
from google.cloud import language_v1
from google.cloud import secretmanager

app = Flask(__name__)

# Initialize Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

# Initialize Natural Language client
language_client = language_v1.LanguageServiceClient()

# Get project ID
project_id = os.environ.get('PROJECT_ID', os.environ.get('GOOGLE_CLOUD_PROJECT'))
slack_channel = os.environ.get('SLACK_CHANNEL', '#feedback-alerts')

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
    """Sends an alert to Slack for non-neutral sentiment."""
    token = get_slack_token()
    
    # Format message based on sentiment
    if sentiment == "positive":
        emoji = ":smile:"
        color = "#36a64f"  # Green
    elif sentiment == "negative":
        emoji = ":disappointed:"
        color = "#ff0000"  # Red
    else:
        return  # Don't send for neutral sentiment
    
    # Prepare Slack message payload
    payload = {
        "channel": slack_channel,
        "attachments": [
            {
                "color": color,
                "pretext": f"New {sentiment} feedback received! {emoji}",
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

@app.route('/', methods=['POST'])
def process_pubsub_message():
    """Process Pub/Sub messages and analyze sentiment."""
    envelope = request.get_json()
    
    # Extract Pub/Sub message
    if not envelope or 'message' not in envelope:
        return 'No Pub/Sub message received', 400
    
    # Decode the message data
    pubsub_message = envelope['message']
    if not pubsub_message.get('data'):
        return 'No data in message', 400
    
    try:
        # Decode and parse the message
        message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
        feedback = json.loads(message_data)
        
        # Analyze sentiment
        sentiment, score = analyze_sentiment(feedback['message'])
        
        # Log the analysis result
        print(f"Feedback analyzed - User: {feedback['user_id']}, Sentiment: {sentiment}, Score: {score}")
        
        # Send Slack alert for non-neutral sentiment
        if sentiment != "neutral":
            send_slack_alert(
                message=feedback['message'],
                sentiment=sentiment,
                score=score,
                user_id=feedback['user_id']
            )
            print(f"Alert sent to Slack for {sentiment} feedback")
        
        return 'Message processed successfully', 200
    
    except Exception as e:
        print(f"Error processing message: {e}")
        return f'Error: {str(e)}', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
