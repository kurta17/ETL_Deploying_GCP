import requests
import json
import time

# Replace with your actual Cloud Run URL
FEEDBACK_RECEIVER_URL = "https://feedback-receiver-XXXX-XX.a.run.app"

# Test payloads
test_payloads = [
    {
        "type": "positive",
        "data": {
            "user_id": "user@example.com",
            "message": "I absolutely love this product! It's made my work so much easier and enjoyable."
        }
    },
    {
        "type": "neutral",
        "data": {
            "user_id": "user2@example.com",
            "message": "The product works fine. It does what it says it will do."
        }
    },
    {
        "type": "negative",
        "data": {
            "user_id": "user3@example.com",
            "message": "I'm disappointed with the service. The response time is terrible and it's full of bugs."
        }
    }
]

# Send requests
for payload in test_payloads:
    print(f"\nSending {payload['type']} feedback...")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        FEEDBACK_RECEIVER_URL,
        headers=headers,
        data=json.dumps(payload['data'])
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Wait 2 seconds between requests
    time.sleep(2)

print("\nAll test requests sent!")
