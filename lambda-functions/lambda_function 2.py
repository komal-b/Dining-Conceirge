import json
import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/475705689657/DiningQueue'

def lambda_handler(event, context):
    print("Lex Event:", json.dumps(event))
    intent = event['sessionState']['intent']['name']
    
    if intent == "GreetingIntent":
        return close("Hi there, how can I help?", intent)
        
    elif intent == "ThankYouIntent":
        return close("You're welcome!", intent)
        
    elif intent == "DiningSuggestionsIntent":
        slots = event['sessionState']['intent']['slots']
        
        location = slots['Location']['value']['interpretedValue']
        cuisine = slots['Cuisine']['value']['interpretedValue']
        time = slots['DiningTime']['value']['interpretedValue']
        people = slots['NumPeople']['value']['interpretedValue']
        email = slots['Email']['value']['interpretedValue']
        
        # Push to SQS
        message = {
            "location": location,
            "cuisine": cuisine,
            "time": time,
            "people": people,
            "email": email
        }
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        
        return close("Thanks! We will email you restaurant suggestions shortly.", intent)

def close(message, intent_name):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": intent_name,
                "state": "Fulfilled"
            }
        },
        "messages": [{
            "contentType": "PlainText",
            "content": message
        }]
    }
