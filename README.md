# Cloud Assignment 1 – Dining Concierge Chatbot
## Team Members
1. Komal Bagwe (knb4003)
2. Tejaswini Pradip Srivastava (tps7866)
   
---
### Overview
This project implements a Dining Concierge Chatbot using AWS services.
The system allows users to chat with a Lex bot to get restaurant recommendations based on location, cuisine, time, and group size. The architecture is built fully serverless using S3, API Gateway, Lambda, Lex, DynamoDB, OpenSearch (ElasticSearch), SES, SQS, and EventBridge.

---
### Part 1 – Static Website Hosting
#### 1A. Setup Static Website**

Enabled Static Website Hosting on S3 bucket:
```cloud-hw1-tejaswini-komal-chatbot (Region: us-east-1)```

Index document: chat.html

***Deployed Website:***
http://cloud-hw1-tejaswini-komal-chatbot.s3-website-us-east-1.amazonaws.com/

#### 1B. Upload Files & Set Permissions

- Uploaded chat.html and assets/ folder
- Disabled Block Public Access
- Made all files public using ACL
- Verified working chatbot UI
---
### Part 2 – Build the Chat API
#### 2A. Import API Spec

- Imported swagger.yaml into API Gateway
- Created endpoint /chatbot (POST) using Lambda Proxy Integration

#### 2B. Create Lambda (LF0 – ChatBotHandler)

- Handles chatbot API requests:
```
return {
  "statusCode": 200,
  "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
  "body": json.dumps(response)
}
```

#### 2C. Enable CORS & SDK

- Enabled CORS (Access-Control-Allow-Origin: *)
-Tested using both curl and frontend integration

- Frontend Fix in chat.js:
```
if (typeof data.body === "string") {
  data = JSON.parse(data.body);
} else if (data.body) {
  data = data.body;
}
```
---

### Part 3 – Amazon Lex V2 Bot

**Lex Setup:**
- Bot Name: DiningConciergeBot
-Language: English (US)

**Intents:**

1. GreetingIntent → “Hi there, how can I help?”
2. ThankYouIntent → “You’re welcome!”
3. DiningSuggestionsIntent → Gathers user preferences

**Lambda (LF1 – DiningBotLambdaHook):**
- Handles intents & pushes requests to SQS
- Responds with: “Thanks! We will email you restaurant suggestions shortly.”

**Slots in DiningSuggestionsIntent**

| Slot        | Type                   |
|--------------|------------------------|
| Location     | AMAZON.City            |
| Cuisine      | CuisineType (Custom)   |
| DiningTime   | AMAZON.Time            |
| NumPeople    | AMAZON.Number          |
| Email        | AMAZON.EmailAddress    |

---
### Part 4 – Lex Integration with Chat API

- Enhanced LF0 to call Lex via boto3.client('lexv2-runtime')
- Forwarded messages to Lex & returned its response to the frontend

**Updated IAM roles:**

- LF0 (lambda_function.py) → AmazonLexRuntimeV2
- LF1 (lambda_function 2.py) → Resource-based policy for Lex invocation
---
### Part 5 – Yelp Data + DynamoDB
**Data Collection:**
- Used Yelp API to collect 1000+ Manhattan restaurants
- Saved as manhattan_restaurants.csv

**DynamoDB Setup:**
```
Table: yelp-restaurants
Partition Key: businessid (String)
```
- Uploaded data using dynamo_db_insert.ipynb with:
```
pip install boto3 pandas tqdm
```
---

### Part 6 – ElasticSearch (OpenSearch) Integration

- Steps

1. Created OpenSearch domain restaurants
2. Enabled Fine-Grained Access Control
3. Created index /restaurants
4. Inserted sample docs:
```
{ "RestaurantID": "123", "Cuisine": "Mexican" }
```
5. Connected ingestion script → reads from DynamoDB, indexes into OpenSearch

---

### Part 7 – Suggestions Module (LF2) - lambda_function 3.py
Components:

| AWS Service | Purpose                                 |
|--------------|------------------------------------------|
| Lambda (LF2) | Processes SQS messages and sends emails  |
| SQS          | Stores pending dining requests           |
| DynamoDB     | Contains restaurant info                 |
| OpenSearch   | Retrieves restaurant suggestions         |
| SES          | Sends suggestion emails                  |
| EventBridge  | Triggers LF2 every minute                |
| CloudWatch   | Logs & debugging                         |

**End-to-End Flow Tested:**
SQS → Lambda → OpenSearch → SES → User Email

---

### (Extra Credit) Dead Letter Queue (DLQ) Implementation
Handle failed email sends (e.g., invalid email addresses).

**Steps:**

1. Created DLQ → DiningQueue-DLQ
2. Attached to main queue (maxReceiveCount = 3)
3. Modified LF2 to not delete messages if email fails
4. Verified message retry → automatic move to DLQ

#### Logs Example:
```
[ERROR] Failed to send email to invalid_email_address:
An error occurred (InvalidParameterValue) when calling SendEmail: Missing final '@domain'
```

---
