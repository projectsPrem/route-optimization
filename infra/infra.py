import boto3

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

def create_orders_table():
    try:
        response = dynamodb.create_table(
            TableName='orders',
            KeySchema=[
                {
                    'AttributeName': 'order_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'order_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand billing
        )
        print("Creating table... Please wait")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='orders')
        print("Table created successfully!")
    except Exception as e:
        print(f"Error creating table: {str(e)}")

if __name__ == "__main__":
    create_orders_table()
