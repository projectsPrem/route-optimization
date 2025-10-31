# backend/app.py
from decimal import Decimal
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv, find_dotenv
import json
from datetime import datetime
from functools import wraps
import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError



# Load environment variables
env_path = find_dotenv()
load_dotenv(env_path)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests for frontend integration

# AWS Cognito configuration
AWS_REGION = os.getenv('AWS_REGION')
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
COGNITO_REGION = os.getenv('COGNITO_REGION')

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
        print(response['AuthenticationResult']['AccessToken'])
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

# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'RouteOrders')
DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION', 'ap-south-1')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Cache for Cognito public keys
cognito_keys = None

# Cognito Issuer URL & JWKS URL
COGNITO_ISSUER = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
JWKS_URL = f'{COGNITO_ISSUER}/.well-known/jwks.json'

# Cache JWKS keys
jwks = requests.get(JWKS_URL).json()

def convert_floats_to_decimal(obj):
    """
    Recursively converts float values in dict or list to Decimal.
    """
    if isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def get_cognito_public_key(token):
    """Get public key from JWKS matching token kid."""
    headers = jwt.get_unverified_header(token)
    kid = headers['kid']
    for key in jwks['keys']:
        if key['kid'] == kid:
            return key
    return None

def verify_token(token):
    try:
        public_key = get_cognito_public_key(token)
        if not public_key:
            raise Exception('Public key not found in JWKS')

        # Decode and verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER
        )
        return payload

    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
    except Exception as e:
        print("Verification error:", str(e))
        return None

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Token missing or invalid'}), 401
        
        access_token = token[len('Bearer '):]
        payload = verify_token(access_token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Set user_id attribute on request
        request.user_id = payload.get('sub')
        request.user_email = payload.get('email')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/orders', methods=['POST'])
@token_required
def create_order():
    """
    Create a new route optimization order
    Expected JSON payload:
    {
        "pickup_location": {"lat": 40.7128, "lng": -74.0060, "address": "..."},
        "delivery_locations": [
            {"lat": 40.7589, "lng": -73.9851, "address": "..."},
            {"lat": 40.7614, "lng": -73.9776, "address": "..."}
        ],
        "vehicle_type": "car",
        "priority": "standard"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['pickup_location', 'delivery_locations']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate unique order ID
        import uuid
        order_id = str(uuid.uuid4())
        
        # Prepare order data
        order_data = {
            'order_id': order_id,
            'user_id': request.user_id,
            'user_email': request.user_email,
            'pickup_location': data['pickup_location'],
            'delivery_locations': data['delivery_locations'],
            'vehicle_type': data.get('vehicle_type', 'car'),
            'priority': data.get('priority', 'standard'),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        order_data = convert_floats_to_decimal(order_data)
        
        # Add optional fields if provided
        optional_fields = ['notes', 'estimated_distance', 'estimated_time']
        for field in optional_fields:
            if field in data:
                order_data[field] = data[field]
        
        # Store in DynamoDB
        response = table.put_item(Item=order_data)
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order_id,
            'order': order_data
        }), 201
        
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Failed to create order', 'details': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@token_required
def get_user_orders():
    """Get all orders for the authenticated user"""
    try:
        # Query orders by user_id
        response = table.query(
            IndexName='user_id-index',  # You'll need to create this GSI
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={
                ':user_id': request.user_id
            }
        )
        
        orders = response.get('Items', [])
        
        return jsonify({
            'success': True,
            'orders': orders,
            'count': len(orders)
        }), 200
        
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch orders', 'details': str(e)}), 500

@app.route('/api/orders/<order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    """Get a specific order by ID"""
    try:
        response = table.get_item(Key={'order_id': order_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Order not found'}), 404
        
        order = response['Item']
        
        # Ensure user owns this order
        if order['user_id'] != request.user_id:
            return jsonify({'error': 'Unauthorized access to order'}), 403
        
        return jsonify({
            'success': True,
            'order': order
        }), 200
        
    except Exception as e:
        print(f"Error fetching order: {str(e)}")
        return jsonify({'error': 'Failed to fetch order', 'details': str(e)}), 500

@app.route('/api/orders/<order_id>', methods=['PUT'])
@token_required
def update_order(order_id):
    """Update order status or details"""
    try:
        data = request.get_json()
        
        # First check if order exists and user owns it
        response = table.get_item(Key={'order_id': order_id})
        
        if 'Item' not in response:
            return jsonify({'error': 'Order not found'}), 404
        
        order = response['Item']
        
        if order['user_id'] != request.user_id:
            return jsonify({'error': 'Unauthorized access to order'}), 403
        
        # Update allowed fields
        update_expression = "SET updated_at = :updated_at"
        expression_values = {
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if 'status' in data:
            update_expression += ", #status = :status"
            expression_values[':status'] = data['status']
        
        if 'optimized_route' in data:
            update_expression += ", optimized_route = :route"
            expression_values[':route'] = data['optimized_route']
        
        # Perform update
        response = table.update_item(
            Key={'order_id': order_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames={'#status': 'status'} if 'status' in data else None,
            ReturnValues='ALL_NEW'
        )
        
        return jsonify({
            'success': True,
            'message': 'Order updated successfully',
            'order': response['Attributes']
        }), 200
        
    except Exception as e:
        print(f"Error updating order: {str(e)}")
        return jsonify({'error': 'Failed to update order', 'details': str(e)}), 500


if __name__ == '__main__':
    # For development only. Use a production-grade WSGI server like Gunicorn.
    app.run(debug=True, port=5001)