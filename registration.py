# backend/app.py
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
env_path = find_dotenv()
load_dotenv(env_path)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests for frontend integration

# AWS Cognito configuration
AWS_REGION = os.getenv('AWS_REGION')
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')

if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID]):
    raise EnvironmentError("One or more required environment variables are missing: "
                           "AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID")

# Initialize the Cognito client
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

@app.route('/signup', methods=['POST'])
def signup():
    """
    Registers a new user in AWS Cognito.
    Expects JSON: { "email": "", "password": "", "name": "" }
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        response = cognito_client.sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": name if name else ""}
            ],
        )
        user_confirmed = response.get('UserConfirmed', False)
        user_sub = response.get('UserSub')
        
        # Return meaningful message whether user needs to confirm email or is confirmed
        if user_confirmed:
            message = "User registered and confirmed successfully."
        else:
            message = "User registered successfully. Please check your email to confirm your account."
        
        return jsonify({
            "message": message,
            "userConfirmed": user_confirmed,
            "userSub": user_sub
        }), 201

    except cognito_client.exceptions.UsernameExistsException:
        return jsonify({"error": "This email address is already registered."}), 409

    except cognito_client.exceptions.InvalidPasswordException as e:
        # Extract meaningful password validation messages
        error_msg = str(e).split(":")[-1].strip()
        return jsonify({"error": f"Invalid password. {error_msg}"}), 400

    except Exception as e:
        # Log the exception internally (could be expanded)
        print(f"Unexpected error in signup: {e}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user with Cognito and returns JWT tokens.
    Expects a JSON body with 'email' and 'password'.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
            }
        )
        # This response contains the IdToken, AccessToken, and RefreshToken
        print(response)
        return jsonify(response['AuthenticationResult']), 200
    except cognito_client.exceptions.NotAuthorizedException:
        return jsonify({'error': 'Invalid email or password.'}), 401
    except cognito_client.exceptions.UserNotFoundException:
        return jsonify({'error': 'This user does not exist.'}), 404
    except cognito_client.exceptions.UserNotConfirmedException:
        return jsonify({'error': 'User is not confirmed. Please check your email.'}), 403
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500






@app.route('/confirm', methods=['POST'])
def confirm_account_creation():
    """
    Authenticates a user with Cognito and returns JWT tokens.
    Expects a JSON body with 'email' and 'code'.
    """
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not all([email, code]):
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        response = cognito_client.confirm_sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
                Username= email,
                ConfirmationCode= code,
        )
        # This response contains the IdToken, AccessToken, and RefreshToken
        return jsonify(response), 200
    except cognito_client.exceptions.NotAuthorizedException:
        return jsonify({'error': 'Invalid email or password.'}), 401
    except cognito_client.exceptions.UserNotFoundException:
        return jsonify({'error': 'This user does not exist.'}), 404
    except cognito_client.exceptions.UserNotConfirmedException:
        return jsonify({'error': 'User is not confirmed. Please check your email.'}), 403
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

# Note: A complete backend would also require:
# 1. A mechanism (like a Flask decorator) to protect other endpoints.
#    This decorator would verify the JWT from the 'Authorization' header.
# 2. Endpoints for password reset, token refresh, etc.
# 3. All the other business logic endpoints (/orders, /routes, etc.).

if __name__ == '__main__':
    # For development only. Use a production-grade WSGI server like Gunicorn.
    app.run(debug=True, port=5001)