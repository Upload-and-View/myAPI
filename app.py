from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- Helper Function (Remains the same) ---
def generate_8bit_binary(message):
    integer_value = len(message) % 256
    binary_string = bin(integer_value)[2:]
    return binary_string.zfill(8)

# --- API Endpoint Definition with Strict Payload ---
@app.route('/forward_message', methods=['POST'])
def forward_message():
    # 1. RECEIVE: Get the data from the initial client (Client A)
    try:
        data = request.get_json()
        
        # Validation
        if not data or 'message' not in data or 'destination_link' not in data:
            return jsonify({"error": "Missing 'message' or 'destination_link' in request body."}), 400
            
    except Exception:
        return jsonify({"error": "Invalid JSON format."}), 400

    user_message = data['message']
    destination_url = data['destination_link'] 

    # 2. PROCESS & TRANSFORM: Create the **STRICT** payload
    binary_value = generate_8bit_binary(user_message)

    # *** CRITICAL CHANGE HERE ***
    # The payload contains ONLY the required structure: {"value": binary_value}
    payload_to_send = {
        "value": binary_value
    }

    # 3. FORWARD: Send the new payload to the dynamic destination URL
    try:
        forward_response = requests.post(
            destination_url,
            json=payload_to_send, # Sending ONLY the strict payload
            timeout=10
        )

        # 4. RESPOND: Report the outcome back to the original client (Client A)
        if 200 <= forward_response.status_code < 300:
            return jsonify({
                "status": "success",
                "message": f"Data successfully sent to {destination_url}.",
                "sent_8bit_value": binary_value,
                "note": "Only the {'value': binary_string} structure was sent to the destination."
            }), 200
        else:
            return jsonify({
                "status": "forward_error",
                "message": f"Destination API returned an error ({forward_response.status_code}).",
                "destination_url": destination_url
            }), 502
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "network_error",
            "message": f"Failed to connect to the provided destination URL: {destination_url}",
            "error_details": str(e)
        }), 504

# IMPORTANT: No need for the __main__ block if deploying with Gunicorn on Render
