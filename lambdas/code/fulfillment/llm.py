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

# model_id            = "anthropic.claude-3-haiku-20240307-v1:0"
model_id            = "anthropic.claude-3-sonnet-20240229-v1:0"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

system_prompt       = """
You are Isidora, a helpful, respectful, and honest assistant for Easy, an online store. 
Your job is to provide information about order status to customers, you can also open an ticket for support or escalate to an agent. Follow these instructions carefully:

1. Always communicate in Spanish and maintain a respectful and polite tone throughout the conversation. Use customer's name if you know it.
2. Your task is to gather the following information from the customer:

   - Name
   - Order number (8-digit sequence like 12345678)
   - RUT (Chilean citizen number, 8 or 9 digits, a dash and a digit or letter, like 10987654-1)

3. If the conversation derails, politely redirect the conversation back to gathering the required information to providing order status.
5. Don't offer refunds or prioritizations, focus on providing accurate order status information.
6. If customer need to solve a problem outside your scope, either explicitly or implicitly, you can open a support ticket.

Keep your messages short without redundacy, because you will be answering the call center where time is short.
"""


first_messages =  [
    { "content": [{ "text": "hola"}], "role": "user"},
    { "content": [
        {"text": "Hola. Buen día, has llamado al servicio al cliente de Easy, hablas con Isidora. Cuéntame ¿cómo puedo ayudarte?"}
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
        },
        {
            "toolSpec": {
                "name": "open_ticket",
                "description": "Open a issue ticket",
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
                            "issue_details": {
                                "type": "string",
                                "description": "Issue description, what is the problem from customer's perspective",
                            },
                        },
                        "required": ["order_number", "identity_document_number"]
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "agent_escalation",
                "description": "Escalates this contact to a support specialist. Use this when customer need to escalate and speak to company representative.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                },
            }
        }
    ]
}


CONVERSATION_TABLE_NAME    = os.environ['CONVERSATION_TABLE_NAME']
ORDER_TABLE_NAME           = os.environ['ORDER_TABLE_NAME']
TICKET_TABLE_NAME          = os.environ['TICKET_TABLE_NAME']


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

def open_ticket(session_id, order_number, rut, description):
    print (f"abriendo ticket")
    table = dynamodb.Table(TICKET_TABLE_NAME)
    
    ticket_number = ''.join(char for char in order_number.split('-')[-1] if char.isdigit())

    item = {
        "issue_number": ticket_number,
        "contact_id": session_id,
        "order_number": order_number,
        "identity_document_number": rut,
        "issue_details": description
    }
    response  = table.put_item(Item=item, ReturnValues= "ALL_OLD")
    if response.get("ResponseMetadata").get("HTTPStatusCode") == 200:
        return f"Hemos creado el ticket {session_id} para seguimiento de este caso." 
    
    return "No se pudo crear el ticket"






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

    while stop_reason == 'tool_use':
        tool_requests = response['output']['message']['content']
        for tool_request in tool_requests:
            if 'toolUse' in tool_request:
                tool = tool_request['toolUse']
                logger.info("Requesting tool %s. Request: %s",
                            tool['name'], tool['toolUseId'])
                tool_result = {}
                print (tool['input'])

                if tool['name'] == 'get_order':
                    res = get_order(tool['input']['order_number'], tool['input']['identity_document_number'])

                elif tool['name'] == 'open_ticket':
                    res = open_ticket(session_id, tool['input']['order_number'], tool['input']['identity_document_number'], tool['input']['issue_details'])
                    
                elif tool['name'] == 'agent_escalation': # This break the loop and escalates to an agent

                    res = "Escalando a agente"
                    print(res)
                    new_messages.append({ 
                        "role": "user", 
                        "content": [{ 
                            "toolResult": { 
                                "toolUseId": tool['toolUseId'],
                                "content": [{
                                    "json": {"result": res}}
                                ]}
                        }]
                    })
                    new_messages.append({ "role": "assistant", "content": [{"text": "Caso Escalado"}]})
                    return "ESCALAMIENTO", new_messages


                print("Result:", res)
                    
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
        stop_reason = response['stopReason']

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

    if assistant_reply == "ESCALAMIENTO":
        intent["name"] = "AgentIntent"
        print("intent_request:", intent_request)
        session_attributes["previous_intent"] = "AgentIntent"
        return dialog.delegate(
            active_contexts, session_attributes, intent,
            #[{'contentType': 'PlainText', 'content': assistant_reply }]
            )

    return dialog.elicit_intent(
        active_contexts, session_attributes, intent, 
        [{'contentType': 'PlainText', 'content': assistant_reply }])
