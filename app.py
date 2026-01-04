from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- GLOBAL STORAGE ---
# This variable will store the last successfully forwarded binary string.
# NOTE: In a production environment, this variable will reset if the server restarts.
LAST_SENT_BINARY = "00000000" 

# --- Helper Function (Remains the same) ---
def generate_8bit_binary(message):
    integer_value = len(message) % 256
    binary_string = bin(integer_value)[2:]
    return binary_string.zfill(8)

# --- NEW: Root Endpoint (GET /) ---
# When you visit the main URL in your browser, it will now return the stored value.
@app.route('/', methods=['GET'])
def get_last_binary():
    # Retrieve the last stored value from the global variable
    return jsonify({
        "value": LAST_SENT_BINARY
    }), 200

# --- Existing: Forwarding Endpoint (POST /forward_message) ---
@app.route('/forward_message', methods=['POST'])
def forward_message():
    global LAST_SENT_BINARY  # <--- Declare use of global variable

    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'destination_link' not in data:
            return jsonify({"error": "Missing 'message' or 'destination_link' in request body."}), 400
            
    except Exception:
        return jsonify({"error": "Invalid JSON format."}), 400

    user_message = data['message']
    destination_url = data['destination_link'] 

    binary_value = generate_8bit_binary(user_message)

    payload_to_send = {
        "value": binary_value
    }

    # 3. FORWARD
    try:
        forward_response = requests.post(destination_url, json=payload_to_send, timeout=10)

        if 200 <= forward_response.status_code < 300:
            # *** CRITICAL ADDITION: STORE THE NEW VALUE ***
            LAST_SENT_BINARY = binary_value 
            
            return jsonify({
                "status": "success",
                "message": f"Data successfully sent to {destination_url}.",
                "sent_8bit_value": binary_value,
                "note": "New binary value stored and available at the root endpoint (GET /)."
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
