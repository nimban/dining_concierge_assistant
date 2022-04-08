import json
import boto3

def lambda_handler(event, context):
    client = boto3.client('lexv2-runtime')
    response = client.recognize_text(
        botId='WHUYFLIVXD',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='test-session1',
        text=event["messages"][0]["unstructured"]["text"]
    )
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "messages": [{
            "type": "unstructured",
            "unstructured": {
                "text": response["messages"][0]["content"]
            }
        }],
        "body": json.dumps("Done.")
    }
