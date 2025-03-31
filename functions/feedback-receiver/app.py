import os
import json
import logging
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Pub/Sub publisher client
try:
    publisher = pubsub_v1.PublisherClient()
    # project_id = os.environ.get('PROJECT_ID', os.environ.get('GOOGLE_CLOUD_PROJECT'))
    project_id = "vital-cathode-454012-k0"
    if not project_id:
        logger.error("PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable not set")
        raise ValueError("PROJECT_ID environment variable is required")
    
    topic_name = os.environ.get('PUBSUB_TOPIC', 'feedback-topic')
    topic_path = publisher.topic_path(project_id, topic_name)
    logger.info(f"Initialized Pub/Sub client with topic: {topic_path}")
except Exception as e:
    logger.error(f"Error initializing Pub/Sub client: {e}")
    # Continue execution, will handle errors in the endpoint

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['POST'])
def receive_feedback():
    try:
        # Get request data
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            data = request.get_json()
            logger.info(f"Received feedback request: {data}")
        else:
            logger.warning(f"Invalid content type: {content_type}")
            return jsonify({"error": "Content-Type must be application/json"}), 415
        
        # Validate input
        if 'user_id' not in data or 'message' not in data:
            logger.warning("Missing required fields in request")
            return jsonify({"error": "JSON must contain user_id and message fields"}), 400
        
        # Prepare message for Pub/Sub
        message_data = {
            "user_id": data['user_id'],
            "message": data['message']
        }
        
        # Publish to Pub/Sub
        try:
            future = publisher.publish(
                topic_path, 
                json.dumps(message_data).encode('utf-8')
            )
            message_id = future.result()
            logger.info(f"Published message with ID: {message_id}")
            
            return jsonify({
                "status": "success",
                "message": f"Feedback received and published to Pub/Sub with ID: {message_id}"
            })
        except Exception as e:
            logger.error(f"Error publishing to Pub/Sub: {e}")
            return jsonify({"error": f"Failed to publish message: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
