import json
import boto3


def form_greeting_response(event):
    return {
        "sessionState":
            {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent":{
                    "state":"Fulfilled",
                    "name":event['sessionState']["intent"]["name"],
                    "message": {'contentType': "PlainText","content": "What?"}
                },
                "messages":[
                    {
                        "contentType":"Plaintext",
                        "content":"Greeting Intent Fulfilled"
                    }
                ]
            }}


def form_thankyou_response(event):
    return {
        "sessionState":
            {
                "dialogAction": {
                    "type": "Delegate"
                },
                "intent":{
                    "state":"Fulfilled",
                    "name":event['sessionState']["intent"]["name"],
                    "message": {'contentType': "PlainText","content": "What?"}
                },
                "messages":[
                    {
                        "contentType":"Plaintext",
                        "content":"Thank You Intent Fulfilled"
                    }
                ]
            }}


def form_confirmation_response(event):
    print("Fulfillment")
    return {
        "sessionState":{
            "dialogAction": {
                "type": "ConfirmIntent"
            },
            "intentName":"DiningSuggestionIntent",
            "slots": event["sessionState"]["intent"]["slots"],
            "intent":{
                "state":"Fulfilled",
                "name":"DiningSuggestionIntent",
                "message": {'contentType': "PlainText","content": "Done with DiningSuggestionsIntent"},
                "slots": event["sessionState"]["intent"]["slots"]
            },
            "messages": [
                {'contentType': "PlainText", "content": "Done with DiningSuggestionsIntent"}
            ]
        }}


def form_elicit_next_slot_response(event):
    return {"sessionState": event["proposedNextState"]}


def close_conversation(event):
    response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": "Please give me a few minutes to find the perfect restaurant to your likings. I will send an Email, once I am finished."
                }
            },
            "intent":{
                "state":"Fulfilled",
                "name":"DiningSuggestionIntent",
                "message": {
                    "contentType": "PlainText",
                    "content": "Please give me a few minutes to find the perfect restaurant to your likings. I will send an Email, once I am finished."
                },
                "slots": event["sessionState"]["intent"]["slots"]
            },
        }
    }

    return response


def get_slots(event):
    print(event['sessionState']["intent"]["slots"])
    city = event['sessionState']["intent"]["slots"]["City"]
    if city:
        if "interpretedValue" in event['sessionState']["intent"]["slots"]["City"]["value"]:
            city = event['sessionState']["intent"]["slots"]["City"]["value"]["interpretedValue"]
    date = event['sessionState']["intent"]["slots"]["Date"]
    if date:
        date = event['sessionState']["intent"]["slots"]["Date"]["value"]["interpretedValue"]
    cuisine = event['sessionState']["intent"]["slots"]["Cuisine"]
    if cuisine:
        cuisine = event['sessionState']["intent"]["slots"]["Cuisine"]["value"]["interpretedValue"]
    num_people = event['sessionState']["intent"]["slots"]["Reservation_Size"]
    if num_people:
        num_people = event['sessionState']["intent"]["slots"]["Reservation_Size"]["value"]["interpretedValue"]
    email = event['sessionState']["intent"]["slots"]["Email"]
    if email:
        email = event['sessionState']["intent"]["slots"]["Email"]["value"]["interpretedValue"]
    return (city, date, num_people, cuisine, email)


def send_message_to_queue(event):
    city, date, num_people, cuisine, email = get_slots(event)
    messageAttributes = {
        'Cuisine': {
            'DataType': 'String',
            'StringValue': cuisine
        },
        'Date': {
            'DataType': 'String',
            'StringValue': date
        },
        'Reservation_size': {
            'DataType': 'Number',
            'StringValue': num_people
        },
        'City': {
            'DataType': 'String',
            'StringValue': city
        },
        'Email': {
            'DataType': 'String',
            'StringValue': email
        }
    }
    print(messageAttributes)
    sqsClient = boto3.resource('sqs')
    queue = sqsClient.get_queue_by_name(QueueName='dining_request_queue')
    response = queue.send_message(MessageBody="Message from Lex", MessageAttributes=messageAttributes)
    print(response)
    return response


def get_slot_value(event, slot_name):
    return event['sessionState']["intent"]["slots"][slot_name]

def process_dining_intent(event):
    state = event['sessionState']["intent"]["state"]
    confirmationState = event['sessionState']["intent"]["confirmationState"]
    city, date, num_people, cuisine, email = get_slots(event)
    if state == 'InProgress' and confirmationState == 'Confirmed':
        print('sending to queue')
        send_message_to_queue(event)
        return close_conversation(event)
    if state == 'InProgress' and confirmationState == 'Denied':
        return close_conversation(event)
    elif city and date and num_people and cuisine and email:
        print('getting confirmation')
        return form_confirmation_response(event)
    else:
        return form_elicit_next_slot_response(event)


def lambda_handler(event, context):
    intent = event['sessionState']["intent"]["name"]
    if intent == "DiningSuggestionIntent":
        return process_dining_intent(event)
    else:
        return {"message": "The intent matched might be wrong."}
