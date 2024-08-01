
import logging
import dialogstate_utils as dialog
import llm


logger = logging.getLogger()

def dispatch(intent_request):
    intent = dialog.get_intent(intent_request)
    intent_name = intent['name']

    if intent_name in ['FallbackIntent', 'llmIntent']:
        next_state = llm.handler(intent_request)
    return next_state




def lambda_handler(event, context):
    print('event: ', event)
    return dispatch(event)
