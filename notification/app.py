import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 1. Reading the three env vars at the top
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
FROM_ADDRESS = os.getenv("FROM_ADDRESS")

@app.route('/send', methods=['POST'])
def send_email():
    # 2. Parsing and validating the incoming JSON
    data = request.get_json()
    
    if not data or 'to' not in data:
        return jsonify({"status": "error", "message": "Missing required field: to"}), 400

    recipient = data.get('to')
    subject = data.get('subject', '')
    body = data.get('body', '')

    # 3. Making the Mailgun call
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": FROM_ADDRESS,
                "to": recipient,
                "subject": subject,
                "text": body
            },
            timeout=10
        )

        # 4. Returning the right response codes
        if response.status_code in (200, 202):
            return jsonify({"status": "sent"}), 200
        else:
            print(f"Mailgun error: {response.status_code} - {response.text}")
            return jsonify({"status": "failed"}), 500


    except requests.exceptions.RequestException as e:
    	print(f"Request to Mailgun failed: {e}")
    	return jsonify({"status": "failed"}), 500

if __name__ == '__main__':
    # Standard Docker-friendly host/port setup
    app.run(host='0.0.0.0', port=5001)
