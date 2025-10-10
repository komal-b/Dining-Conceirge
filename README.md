# Cloud HW1 – Dining Concierge Chatbot

This project implements a **Dining Concierge Chatbot** using various AWS services including **Amazon Lex**, **Lambda**, **API Gateway**, **SQS**, and **OpenSearch (ElasticSearch)**. It is structured to simulate a real-world conversational assistant that collects restaurant preferences from users and logs the requests for downstream processing.

---

## Repository Structure
```
cloud-hw1-starter/
├── frontend/ # React frontend to interact with the chatbot
│ └── index.html, assets/ ...
├── lambda-functions/ # All Lambda function code
│ ├── LF0_ChatAPI/ # API Lambda that integrates with Lex
│ ├── LF1_LexHandler/ # Lex fulfillment Lambda
│ └── LF2_DummyWorker/ # Dummy worker to process SQS messages
├── other-scripts/
│ └── swagger.yaml # OpenAPI specification for API Gateway
│ └── test-curl.sh # Example cURL commands to test
└── README.md # Project documentation
```

---
## Authors
1. Tejaswini Pradip Srivastava - tps7866
2. Komal Bagwe - knb4003

---

## Components Overview

### 1. Amazon Lex Bot — *DiningConciergeBot*
A conversational chatbot built with **Amazon Lex V2**.

**Intents Implemented:**
- `GreetingIntent` → Responds with a friendly greeting  
- `DiningSuggestionsIntent` → Collects details:
  - Location  
  - Cuisine  
  - Dining Time  
  - Number of People  
  - Email  
- `ThankYouIntent` → Ends conversation politely

**Code Hook (Fulfillment Lambda):**  
`LF1_LexFulfillment.py`  
- Extracts slots from Lex input  
- Pushes structured message (location, cuisine, time, people, email) into **SQS Queue**

---

### 2. Lambda Functions

| Function | Name | Description |
|-----------|------|-------------|
| **LF0** | `LF0_APIGatewayLexTrigger.py` | Handles `/chatbot` API endpoint. Extracts user text, sends it to Lex, and returns the bot response. |
| **LF1** | `LF1_LexFulfillment.py` | Fulfillment Lambda for Lex. Handles intents, extracts slot values, and pushes messages to SQS. |
| **LF2** | `LF2_SQSWorker.py` | (Optional) Reads from SQS for later use (e.g., integration with Yelp API). |

---

### 3. API Gateway Integration
The REST API connects the web frontend and Lex bot.

**Base URL: https://regfzaa1i4.execute-api.us-east-1.amazonaws.com/dev/chatbot**

**Test Example (via curl):**
```
curl -X POST https://regfzaa1i4.execute-api.us-east-1.amazonaws.com/dev/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "type": "unstructured",
      "unstructured": {
        "text": "Find me a place to eat"
      }
    }]
  }'
```
**Response Example:**
```
{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"messages\":[{\"type\":\"unstructured\",\"unstructured\":{\"text\":\"Hi there, how can I help?\"}}]}"
}
```
### 4. Amazon SQS — DiningQueue
Queue name: DiningQueue
Receives user requests from LF1 (Lex Fulfillment)
Message format:
```
{
  "location": "Manhattan",
  "cuisine": "Italian",
  "time": "7 PM",
  "people": "2",
  "email": "user@example.com"
}
```

### 5. OpenSearch (Elasticsearch)
Domain name: restaurants
Index: restaurants
Type: Restaurant
Fields:
- RestaurantID
- Cuisine
Example entries:
```
{ "RestaurantID": "101", "Cuisine": "Italian" }
{ "RestaurantID": "102", "Cuisine": "Mexican" }
{ "RestaurantID": "103", "Cuisine": "Indian" }
{ "RestaurantID": "104", "Cuisine": "Japanese" }
{ "RestaurantID": "105", "Cuisine": "Chinese" }
```
Fine-Grained Access Control Enabled:

- Master user created for secure access
- Access policy restricted to authenticated users

### 6. Frontend — Hosted on AWS S3
A simple web UI that connects to the API Gateway and interacts with Lex in real time.
URL:
http://cloud-hw1-tejaswini-komal-chatbot.s3-website-us-east-1.amazonaws.com/

**How it works:**

1. User types a message
2. JS SDK calls /chatbot endpoint
3. LF0 sends text to Lex → Lex responds
4. Chat interface displays the response dynamically


### IAM Configuration
To enable service communication:
```
LF0 → AmazonLexRuntimeV2FullAccess
LF1 → AmazonSQSFullAccess
LF2 → AmazonSQSFullAccess, OpenSearchAccess
Lex bot → Permission to invoke LF1
API Gateway → Connected with LF0 Lambda Integration
S3 bucket policy → Public read access for website hosting
```

### How Each Component Connects
```
Frontend (S3)
    ↓
API Gateway  →  LF0 (Chat API)
    ↓
Amazon Lex  →  LF1 (Fulfillment Lambda)
    ↓
Amazon SQS (DiningQueue)
    ↓
OpenSearch (stores restaurant data)
```

### Useful Scripts (under /other-scripts)
This directory contains supporting scripts and data files that were used for data extraction, transformation, and API schema definition.

| File / Folder                 | Description                                                                  |
| ----------------------------- | ---------------------------------------------------------------------------- |
| `restaurant_extraction.ipynb` | Jupyter Notebook to scrape or extract restaurant data from external sources. |
| `manhattan_restaurants.csv`   | Raw dataset containing scraped restaurant details (e.g., ID, Cuisine).       |
| `dynamo_db_insert.ipynb`      | Script to insert restaurant records into DynamoDB.                           |
| `populate_es.ipynb`           | Script to insert restaurant data into the AWS Elasticsearch index.           |
| `swagger/`                    | Contains the `swagger.yaml` file defining the OpenAPI schema for the API.    |

---
### Summary
This project demonstrates the integration of AWS Cloud services into a complete conversational pipeline:
- A Lex-based chatbot
- Real-time API integration via Lambda
- Event-driven message queueing with SQS
- Searchable restaurant data via OpenSearch
- Interactive frontend hosted on S3

Together, these components represent a scalable, serverless chatbot system.

