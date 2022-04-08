import json
import boto3
from botocore.vendored import requests
import random

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/686963384763/dining_request_queue"
OPENSEARCH_URL = "https://search-restaurant-data-7zog3yqyt7xojdyt6u3n3o7tc4.us-east-1.es.amazonaws.com"

def get_message_from_queue():
    sqsClient = boto3.client('sqs')
    queue_response = sqsClient.receive_message(
        QueueUrl=QUEUE_URL,
        AttributeNames=['All'],
        MessageAttributeNames = ['All'],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    return queue_response['Messages'][0]


def delete_message_from_queue(recieptHandle):
    sqsClient = boto3.client('sqs')
    response = sqsClient.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=recieptHandle
    )
    return response


def query_OS(cuisine):
    host = OPENSEARCH_URL
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    credentials = requests.auth.HTTPBasicAuth('nimban', 'Trouble911!')
    query = {
        "size": 10,
        "query": {
            "multi_match": {
                "query": cuisine,
                "fields": ["cuisine"]
            }
        }
    }
    headers = {"Content-Type": "application/json"}
    return requests.get(url, auth=credentials, headers=headers, data=json.dumps(query))


def get_restaurants_from_OS(cuisine):
    es_response = query_OS(cuisine)
    restaurants = es_response.json()['hits']['hits']
    return [restaurant['_id'] for restaurant in random.choices(restaurants, k=3)]


def get_restaurant_data_from_Dynamo(restaurants):
    dynamoClient = boto3.client('dynamodb')
    restaurantsData = []
    for id in restaurants:
        response = dynamoClient.get_item(
            TableName="restaurants_yelp",
            Key={"id": {"S": id}}
        )
        restaurantsData.append(response['Item'])
    print(restaurantsData)
    return restaurantsData


def email_suggestions(restaurantsData, email):
    sesClient = boto3.client('ses')
    subject = "Restaurant Recommendations for you"
    intro_message = "Here are some restaurant recommendations based on your requirements from Dining Concierge Service- \n\n\n"
    restaurants_message = ""
    for i, restaurant in enumerate(restaurantsData):
        name = restaurant['name']['S']
        cuisine = restaurant['cuisine']['S']
        address = ""
        for add in restaurant['location']['M']['display_address']['L']:
            address += add['S']
            address += ", "
        num_reviews = restaurant['review_count']['N']
        ratings = restaurant['rating']['N']
        restaurants_message += "\t{}) {}, Address: {}, Cuisine: {}, Ratings: {}, Reviews: {} \n\n".format(i, name, address, cuisine, ratings, num_reviews)

    return sesClient.send_email(
        Source="niranjan119n@gmail.com",
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Text': {'Data': intro_message + restaurants_message, 'Charset': 'UTF-8'}
            }
        }
    )


def lambda_handler(event, context):
    diningReq = get_message_from_queue()
    if diningReq is None:
        return None
    else:
        restaurants = get_restaurants_from_OS(diningReq["MessageAttributes"]["Cuisine"]["StringValue"])
        restaurantsData = get_restaurant_data_from_Dynamo(restaurants)
        notifyResponse = email_suggestions(restaurantsData, "nero91n@gmail.com")  #restaurantsData, diningReq.email)
        return delete_message_from_queue(diningReq["ReceiptHandle"])