from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- GLOBAL STORAGE ---
# This variable stores the last successfully forwarded binary string.
# It resets to 00000000 when the server is restarted (e.g., via Deploy Hook).
LAST_SENT_BINARY = "00000000" 

# --- Helper Function: Character-to-Binary Encoding ---
def generate_8bit_binary(message):
    """Encodes the first character of the message into an 8-bit binary string (ASCII)."""
    if not message:
        return "00000000"

    # Get the first character
    first_char = message[0] 
    
    # Get the ASCII/Unicode decimal value (e.g., 'A' is 65)
    integer_value = ord(first_char) 
    
    # Convert decimal value to binary string, removing the '0b' prefix
    binary_string = bin(integer_value)[2:]
    
    # Pad with zeros to ensure it is exactly 8 bits long
    return binary_string.zfill(8)

# --- Endpoint 1: Retrieve Last Binary Value (GET /) ---
@app.route('/', methods=['GET'])
def get_last_binary():
    """Returns the last stored 8-bit binary value."""
    # Retrieve the last stored value from the global variable
    return jsonify({
        "value": LAST_SENT_BINARY
    }), 200

# --- Endpoint 2: Forward Message (POST /forward_message) ---
@app.route('/forward_message', methods=['POST'])
def forward_message():
    """
    Accepts a message, encodes the first char to binary, and forwards 
    the binary value to the destination_link.
    """
    global LAST_SENT_BINARY  # Must declare to modify the global variable

    # 1. Input Validation and Parsing
    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'destination_link' not in data:
            return jsonify({"error": "Missing 'message' or 'destination_link' in request body."}), 400
            
    except Exception:
        return jsonify({"error": "Invalid JSON format."}), 400

    user_message = data['message']
    destination_url = data['destination_link'] 

    # 2. Process Data
    binary_value = generate_8bit_binary(user_message)

    payload_to_send = {
        "value": binary_value
    }

    # 3. FORWARD to Destination
    try:
        # Use a reasonable timeout for the external request
        forward_response = requests.post(destination_url, json=payload_to_send, timeout=10)

        # Check for success status codes (2xx)
        if 200 <= forward_response.status_code < 300:
            
            # *** UPDATE GLOBAL STATE ON SUCCESS ***
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
        # Handle network issues (e.g., DNS failure, connection timeout)
        return jsonify({
            "status": "network_error",
            "message": f"Failed to connect to the provided destination URL: {destination_url}",
            "error_details": str(e)
        }), 504

if __name__ == '__main__':
    # In a Render environment, Gunicorn handles the running, 
    # but this is for local testing convenience.
    app.run(debug=True)
