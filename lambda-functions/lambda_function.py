import json
import boto3

bot_id = "NAP2ZKWODT"            
bot_alias_id = "DCAHYUPOOL"    # DevAlias
locale_id = "en_US"

lex = boto3.client("lexv2-runtime")

def lambda_handler(event, context):
    try:
        print("Event:", event)

        # Parse body
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        elif isinstance(body, dict):
            pass
        else:
            body = event

        user_input = body["messages"][0]["unstructured"]["text"]
        print("User input:", user_input)

        # Call Lex bot
        response = lex.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId=locale_id,
            sessionId="testuser",  # use a unique ID per user in production
            text=user_input
        )
        print("Lex response:", response)

        # Extract message text from Lex response
        messages = []
        if "messages" in response:
            for msg in response["messages"]:
                messages.append({
                    "type": "unstructured",
                    "unstructured": {
                        "text": msg["content"]
                    }
                })

        # Default fallback
        if not messages:
            messages = [{
                "type": "unstructured",
                "unstructured": {
                    "text": "Sorry, I didn’t understand that."
                }
            }]

        # Return in API Gateway format
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({ "messages": messages })
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "messages": [{
                    "type": "unstructured",
                    "unstructured": {
                        "text": "Oops, something went wrong. Please try again."
                    }
                }]
            })
        }