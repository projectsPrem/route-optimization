import os
import requests
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

# --- Configuration ---
# Get the ORS API Key from environment variables
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjJkNWQ4NDgzMTI0MTRmMzJhM2ZjNTNiOTAyZTljNjY5IiwiaCI6Im11cm11cjY0In0="
if not ORS_API_KEY:
    # Use a placeholder if not set, but the API call will fail.
    # This check is important for startup clarity.
    print("WARNING: ORS_API_KEY environment variable is not set. API calls will fail.")
    ORS_API_KEY = "YOUR_API_KEY_HERE"


ORS_OPTIMIZATION_URL = "https://api.openrouteservice.org/optimization"

app = Flask(__name__)
CORS(app) 

@app.route('/optimize-route', methods=['POST'])
def optimize_route():
    """Proxies the Vroom/ORS optimization request."""
    app.logger.info("Received request for route optimization.")

    # 1. Safely parse JSON payload. 
    optimization_payload = request.get_json(silent=True)

    # 2. Check for missing or malformed JSON data (Crucial for 400 error)
    if not optimization_payload:
        error_message = "Missing or malformed JSON body. Ensure Content-Type is 'application/json' and the body is valid."
        app.logger.error(error_message)
        return jsonify({"error": error_message}), 400

    # 3. Define headers for the ORS API call
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json, application/geo+json'
    }

    try:
        # 4. Forward the request to the ORS Optimization endpoint
        ors_response = requests.post(
            ORS_OPTIMIZATION_URL,
            headers=headers,
            json=optimization_payload,
            timeout=30 
        )
        print(optimization_payload)
        # 5. Check if the ORS API returned an error status code
        ors_response.raise_for_status()

        # 6. Return the JSON solution from ORS to the client
        ors_solution = ors_response.json()
        print(ors_solution)
        app.logger.info("Successfully received optimization solution from ORS.")
        return jsonify(ors_solution), ors_response.status_code

    except requests.exceptions.HTTPError as e:
        # Handle errors from the external ORS API
        error_details = {}
        try:
            error_details = ors_response.json()
        except requests.exceptions.JSONDecodeError:
            error_details['message'] = ors_response.text

        app.logger.error(f"ORS API HTTP Error {ors_response.status_code}: {e}")
        return jsonify({
            "error": "Optimization API returned an error.",
            "status_code": ors_response.status_code,
            "details": error_details
        }), ors_response.status_code

    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, etc.
        app.logger.error(f"Network error or timeout occurred: {e}")
        return jsonify({"error": f"Internal server error: Could not reach optimization service. {e}"}), 503

@app.route('/', methods=['GET'])
def home():
    """Serves the frontend file."""
    try:
        # Flask assumes 'index.html' is in a 'static' folder
        return app.send_static_file('index.html')
    except:
        return jsonify({
            "status": "Running",
            "message": "Backend proxy is active. Copy index.html to the 'static' folder for the full experience."
        })


if __name__ == '__main__':
    # When running locally, Flask is in debug mode.
    # In a production environment (like a container), use a proper WSGI server (e.g., Gunicorn).
    app.run(debug=True, host='0.0.0.0', port=8000)
