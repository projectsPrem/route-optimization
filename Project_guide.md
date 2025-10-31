1. Overview

The backend service manages user authentication, order creation, route optimization, delivery tracking, and notifications. It integrates multiple AWS services to ensure scalability, reliability, and event-driven processing.

2. System Components
Component	Description
Flask (Backend)	REST API layer deployed on Elastic Beanstalk. Handles all client requests, logic, and integration with AWS.
AWS Cognito	Manages user signup, login, and authentication.
AWS DynamoDB	Stores user data, order details, route assignments, and delivery statuses.
AWS S3	Stores uploaded CSV files or route reports.
AWS SQS	Manages asynchronous route optimization tasks.
AWS SNS	Sends email notifications to customers and delivery agents.
AWS CloudWatch	Monitors system metrics, logs, and errors.
3. Actors / Roles
Role	Description
Customer	Places delivery requests, tracks delivery progress, and receives delivery updates.
Delivery Agent / Vehicle	Assigned to optimized delivery routes, marks deliveries as completed.
4. Functional Requirements
4.1 User Authentication

FR1.1: Register and authenticate users (customers and delivery agents) via AWS Cognito.

FR1.2: Support login, logout, password reset, and role-based access control.

FR1.3: JWT token-based authentication for all API requests.

4.2 Order Management

FR2.1: Customers can create new delivery orders with pickup and drop-off details.

FR2.2: Orders are stored in DynamoDB with status fields:

pending, assigned, in_progress, delivered

FR2.3: When an order is created, it is added to an SQS queue for route optimization processing.

4.3 Route Optimization

FR3.1: Flask backend consumes messages from SQS to process route optimization using OpenRouteService or Google Route Optimization API.

FR3.2: Optimized route data (sequence, ETA, distance, coordinates) is stored in DynamoDB.

FR3.3: Assign the optimized route to a specific delivery agent.

FR3.4: Notify the delivery agent via SNS email about the assigned route.

4.4 Delivery Execution and Tracking

FR4.1: Delivery agent fetches assigned routes using /routes/{agent_id} API.

FR4.2: For each delivery point in the route, the agent can mark the order as “Delivered” using an API endpoint.

Example: PUT /orders/{order_id}/status → { "status": "delivered" }

FR4.3: Once the agent marks an order as delivered:

The order status in DynamoDB is updated to delivered.

SNS sends an email notification to the customer confirming successful delivery.

FR4.4: When all deliveries in a route are completed, the route status changes to completed.

4.5 File Upload and S3 Integration

FR5.1: Customers can upload bulk orders as CSV files.

FR5.2: Backend generates presigned S3 URLs for upload.

FR5.3: Once uploaded, an SQS event triggers ingestion of order data into DynamoDB.

4.6 Notifications (SNS)

FR6.1: Send email notification to delivery agent when a route is assigned.

FR6.2: Notify customer when:

Order is assigned for delivery.

Order is successfully delivered.

FR6.3: Notifications are handled through SNS topics with appropriate subscriptions.
. API Endpoints (Examples)
Method	Endpoint	Description
POST	/signup	Register new user via Cognito
POST	/login	Login and get JWT token
POST	/orders	Create new delivery order
GET	/orders/{order_id}	Get specific order details
PUT	/orders/{order_id}/status	Update delivery status (delivered, in_progress)
GET	/routes/{agent_id}	Get optimized route for delivery agent
POST	/upload-url	Generate S3 presigned upload URL