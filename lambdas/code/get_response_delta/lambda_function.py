import time
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key

logger                  = logging.getLogger()
dynamodb                = boto3.resource('dynamodb')

PARTIAL_MESSAGES_TABLE  = os.environ['PARTIAL_MESSAGES_TABLE']


def wait_until_next_message(contactId, max_iter = 10):
    current_iter = 0
    while current_iter < max_iter:
        message = get_message(contactId)
        if message:
            print("Message:", message)
            print("Iter:", current_iter)
            return message
        current_iter += 1
        time.sleep(0.25)
    
    return {"say": "NO_MESSAGES"}



def get_message(contactId):
    table = dynamodb.Table(PARTIAL_MESSAGES_TABLE)
    response = table.query(
        KeyConditionExpression=Key("ContactId").eq(contactId),
        ScanIndexForward=True,
        Limit=1,
    )
    items = response["Items"]
    if len(items): 
        return items[0]
    return None


def delete_message(key):
    table = dynamodb.Table(PARTIAL_MESSAGES_TABLE)
    table.delete_item(Key=key)


def lambda_handler(event, context):
    print('event: ', event)

    contact_data = event.get("Details").get("ContactData")

    if not contact_data: return

    contact_id = contact_data.get("ContactId")

    next_phrase = wait_until_next_message(contact_id)
        
    say = next_phrase.get("text")
    if next_phrase.get("timestamp"):
        print("Delete", delete_message({"ContactId":contact_id, "timestamp":  next_phrase.get("timestamp")}))
        
    print ("Delta:",say)
    return {"say": f"<speak>{say}</speak>"}


