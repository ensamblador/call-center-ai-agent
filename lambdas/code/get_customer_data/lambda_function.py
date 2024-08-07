import time
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key

logger                  = logging.getLogger()
dynamodb                = boto3.resource('dynamodb')

ORDER_TABLE_NAME           = os.environ['ORDER_TABLE_NAME']

def get_customer_data(phone_number):
    table = dynamodb.Table(ORDER_TABLE_NAME)
    response = table.query(
        IndexName="phone_number",
        KeyConditionExpression=Key("phone_number").eq(phone_number),
        ScanIndexForward=True,
        Limit=1,
    )
    items = response["Items"]
    if len(items): 
        return items[0]
    return None

def lambda_handler(event, context):
    print('event: ', event)

    contact_data = event.get("Details").get("ContactData")
    if not contact_data: return
    
    channel = contact_data.get("Channel")
    if channel != "VOICE": return

    customer_endpoint = contact_data.get("CustomerEndpoint").get("Address")
    if not customer_endpoint: return

    customer_data = get_customer_data(customer_endpoint.replace("+", ""))
    if customer_data:
        return customer_data
    else:
        return {"order_number": "NONE"}