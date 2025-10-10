import json
import boto3
import random
import requests
from requests_aws4auth import AWS4Auth

# --- AWS Clients ---
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

# --- Configurations ---
SQS_URL = "https://sqs.us-east-1.amazonaws.com/475705689657/DiningQueue"
ES_HOST = "https://search-restaurants-rgucpr3whjjvho6cfxx442h7l4.aos.us-east-1.on.aws"
TABLE_NAME = "yelp-restaurants"
SENDER_EMAIL = "knb4003@nyu.edu"

# --- AWS4Auth for Elasticsearch ---
session = boto3.session.Session()
credentials = session.get_credentials()
region = session.region_name or 'us-east-1'
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    'es',
    session_token=credentials.token
)

# --- Helper functions ---
def get_random_restaurant_from_es(cuisine):
    """Return a random restaurant ID matching the cuisine from Elasticsearch"""
    query = {"query": {"match": {"cuisine": cuisine}}}
    url = f"{ES_HOST}/_search"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query), timeout=5)
        response.raise_for_status()
        data = response.json()
        hits = data.get('hits', {}).get('hits', [])
        if not hits:
            return None
        return random.choice(hits)['_source']['RestaurantID']
    except Exception as e:
        print(f"Error querying ES: {e}")
        return None

def get_restaurant_details_from_dynamo(restaurant_id):
    """Fetch restaurant details from DynamoDB"""
    table = dynamodb.Table(TABLE_NAME)
    try:
        response = table.get_item(Key={"business_id": restaurant_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error querying DynamoDB: {e}")
        return None

def send_email(recipient, restaurant):
    """Send restaurant suggestion email via SES"""
    subject = f"Your {restaurant['cuisine']} Restaurant Recommendation 🍜"
    body_text = (
        f"Hi there!\n\n"
        f"Here's a {restaurant['cuisine']} restaurant you might enjoy:\n\n"
        f"Name: {restaurant['name']}\n"
        f"Address: {restaurant['address']}\n"
        f"Rating: {restaurant.get('rating', 'N/A')}\n\n"
        f"Enjoy your meal!\n"
    )
    try:
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}}
            }
        )
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        raise

# --- Lambda handler ---
def lambda_handler(event, context):
    print("Lambda triggered by EventBridge")

    # Poll messages from SQS
    try:
        messages = sqs.receive_message(
            QueueUrl=SQS_URL,
            MaxNumberOfMessages=10,  # Poll up to 10 messages at a time
            WaitTimeSeconds=0
        )
    except Exception as e:
        print(f"Error receiving messages from SQS: {e}")
        return {"status": "error"}

    if 'Messages' not in messages:
        print("No messages in queue")
        return {"status": "empty"}

    # Process each message
    for msg in messages['Messages']:
        try:
            body = json.loads(msg['Body'])
            email = body.get('email')
            cuisine = body.get('cuisine')
            print(f"Processing request: email={email}, cuisine={cuisine}")

            # Get random restaurant from Elasticsearch
            restaurant_id = get_random_restaurant_from_es(cuisine)
            if not restaurant_id:
                print(f"No restaurant found for cuisine {cuisine}")
                continue

            # Get restaurant details from DynamoDB
            restaurant = get_restaurant_details_from_dynamo(restaurant_id)
            if not restaurant:
                print(f"No DynamoDB details found for restaurant_id {restaurant_id}")
                continue

            try:
                # Send email via SES
                send_email(email, restaurant)
                print(f"Email sent successfully to {email}")


                # Delete processed message from SQS
                sqs.delete_message(
                    QueueUrl=SQS_URL,
                    ReceiptHandle=msg['ReceiptHandle']
                )
                print(f"Message deleted from SQS")

            except Exception as ses_error:
                # Don't delete message, allow SQS retry and eventual DLQ
                print(f"Failed to send email for requestId={msg['MessageId']}: {ses_error}")
                raise

        except Exception as e:
            print(f"Error processing message: {e}")
            continue

    return {"status": "processed", "processed_messages": len(messages.get('Messages', []))}
