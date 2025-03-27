import os
import json
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1

app = Flask(__name__)

# Initialize Pub/Sub publisher client
publisher = pubsub_v1.PublisherClient()
project_id = os.environ.get('PROJECT_ID', os.environ.get('GOOGLE_CLOUD_PROJECT'))
topic_path = publisher.topic_path(project_id, 'feedback-topic')

@app.route('/', methods=['POST'])
def receive_feedback():
    # Get request data
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        data = request.get_json()
    else:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    # Validate input
    if 'user_id' not in data or 'message' not in data:
        return jsonify({"error": "JSON must contain user_id and message fields"}), 400
    
    # Prepare message for Pub/Sub
    message_data = {
        "user_id": data['user_id'],
        "message": data['message']
    }
    
    # Publish to Pub/Sub
    future = publisher.publish(
        topic_path, 
        json.dumps(message_data).encode('utf-8')
    )
    message_id = future.result()
    
    return jsonify({
        "status": "success",
        "message": f"Feedback received and published to Pub/Sub with ID: {message_id}"
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
