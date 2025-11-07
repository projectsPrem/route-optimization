import boto3

ssm = boto3.client('ssm', region_name='ap-south-1')

response = ssm.get_parameter(
    Name='google_api_key',
    WithDecryption=False)

print(response.get('Parameter').get('Value'))

