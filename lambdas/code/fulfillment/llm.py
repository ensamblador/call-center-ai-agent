import dialogstate_utils as dialog
import logging
import boto3
import json
import os
import time
from decimal import Decimal

print (boto3.__version__)


bedrock_client      = boto3.client('bedrock-runtime')
dynamodb            = boto3.resource('dynamodb')

model_id            = "anthropic.claude-3-haiku-20240307-v1:0"
model_id            = "anthropic.claude-3-sonnet-20240229-v1:0"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

system_prompt       = """
You are Isidora, a helpful, respectful, and honest assistant for Easy, an online store. 
Your job is to provide information about order status to customers. Follow these instructions carefully:

1. Always communicate in Spanish and maintain a respectful and polite tone throughout the conversation.
2. Your task is to gather the following information from the customer:

   - Last name
   - Order number (8-digit sequence)
   - RUT (Chilean citizen number)

3. Follow these steps to gather and format the information:
   a. If any information is missing, politely ask the customer for it.
   b. Format the RUT as follows:
      - Remove any dots or spaces
      - Ensure there's a dash before the last digit
      - The last digit can be a number or the letter 'K'
      - Example: "10.172.747-5" or "10 172 747 5" should be formatted as "10172747-5"
   c. For the last name, if you're unsure about the spelling, politely ask the customer to clarify.
   e. Verify that the order number is an 8-digit sequence.

4. If the conversation derails, politely redirect the conversation back to gathering the required information to providing order status."""


first_messages =  [
    { "content": [{ "text": "hola"}], "role": "user"},
    { "content": [
        {"text": "Hola. Buen día, has llamado al servicio al cliente de Easy, hablas con Isidora. Cuéntame como ¿puedo ayudarte? "}
        ],"role": "assistant"
    }
]



tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_order",
                "description": "Get order data",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "order_number": {
                                "type": "string",
                                "description": "8-digit order number",
                            },
                            "identity_document_number": {
                                "type": "string",
                                "description": "customer identity_document_number as 8 consecutive digits, a dash and a character (K or digit)",
                            },
                        },
                        "required": ["order_number", "identity_document_number"]
                    }
                },
            }
        }
    ]
}


CONVERSATION_TABLE_NAME      = os.environ['CONVERSATION_TABLE_NAME']
ORDER_TABLE_NAME           = os.environ['ORDER_TABLE_NAME']

def not_meaningful(user_utterance):
    if user_utterance == '' or len(user_utterance) < 3:
        return True
    return False


def get_order(order_number, rut):
    print (f"obteniendo {order_number} de la base de datos")
    table = dynamodb.Table(ORDER_TABLE_NAME)
    response  = table.get_item(Key={"order_number": order_number})
    item = response.get("Item")
    if item:
        print ("Item:", response.get("Item"))
        if item.get("identity_document_number") == rut:
            status = item.get("status")
            delivery_date = item.get("delivery_date")
            shipping_address = item.get("shipping_address")
            return f"""Pedido {order_number} se encuentra en estado {status} con fecha de envío para {delivery_date} a la dirección {shipping_address}"""
        else:
            return "RUT incorrecto"
    else:
        return "Pedido no encontrado"



def call_llm_with_tools(session_id, user_input, messages =[]):
    new_messages = [m for m in messages]
    new_messages.append({"role": "user","content": [{"text": user_input}]})
    
    print (new_messages)
    
    response = bedrock_client.converse(
        modelId=model_id,
        system = [{"text": system_prompt}],
        messages=new_messages,
        toolConfig=tool_config
    )

    output_message = response['output']['message']
    new_messages.append(output_message)
    stop_reason = response['stopReason']


    if stop_reason == 'tool_use':
        # Tool use requested. Call the tool and send the result to the model.
        tool_requests = response['output']['message']['content']
        for tool_request in tool_requests:
            if 'toolUse' in tool_request:
                tool = tool_request['toolUse']
                logger.info("Requesting tool %s. Request: %s",
                            tool['name'], tool['toolUseId'])

                if tool['name'] == 'get_order':
                    tool_result = {}
                    print (tool['input'])
                    res = get_order(tool['input']['order_number'], tool['input']['identity_document_number'])
                    tool_result = {
                        "toolUseId": tool['toolUseId'],
                        "content": [{"json": {"result": res}}]
                    }
      

                    tool_result_message = {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": tool_result

                            }
                        ]
                    }
                    new_messages.append(tool_result_message)

                    # Send the tool result to the model.
                    response = bedrock_client.converse(
                        modelId=model_id,
                        messages=new_messages,
                        toolConfig=tool_config
                    )
                    output_message = response['output']['message']
                    new_messages.append(output_message)

    return output_message['content'][0]['text'], new_messages


def get_item(table_name, key):
    table = dynamodb.Table(table_name)
    response  = table.get_item(Key=key)
    return response.get('Item')


def get_chat_history(sessionId):
    key = {"sessionId": sessionId}
    if sessionId:
        current_history = get_item(CONVERSATION_TABLE_NAME, key)
        if current_history:
            print("Hay Chat History")
            return current_history
    
    print ("No hay Chat History")

    messages = []

    return dict(**key,  messages= messages)


def put_chat_history(item):
    print (f"Guardando en DynamoDB: {item}")
    table = dynamodb.Table(CONVERSATION_TABLE_NAME)
    response  = table.put_item(Item=item)
    return response


def handler(intent_request):
    intent = dialog.get_intent(intent_request)
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)

    user_utterance = intent_request['inputTranscript']
    if user_utterance == "" :
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent, 
            [{'contentType': 'PlainText', 'content': "Hola, no entendí lo que dijiste, puedes repetir?"}])

    session_id = intent_request.get('sessionId')
    if (intent_request.get("inputMode") == "Text") and (intent_request.get("sessionState").get("sessionAttributes")):
        session_attributes = intent_request.get("sessionState").get("sessionAttributes")
        if session_attributes.get("ContactId"):
            session_id = session_attributes.get("ContactId")


    chat_history = get_chat_history(session_id)

    assistant_reply, new_messges = call_llm_with_tools(session_id, user_utterance, messages=chat_history['messages'])
    
    chat_history['messages'] = new_messges

    put_chat_history(chat_history)


    return dialog.elicit_intent(
        active_contexts, session_attributes, intent, 
        [{'contentType': 'PlainText', 'content': assistant_reply }])
