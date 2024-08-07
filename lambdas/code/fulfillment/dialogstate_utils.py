"""
Standard util methods to manage dialog state
"""

import traceback
import json

def remove_inactive_context(context_list):
    if not context_list:
        return context_list
    new_context = []
    for context in context_list:
        time_to_live = context.get('timeToLive')
        if  time_to_live and time_to_live.get('turnsToLive') != 0:
            new_context.append(context)
    return new_context


def close(active_contexts, session_attributes, intent, messages):
    active_contexts = remove_inactive_context(active_contexts)
    intent['state'] = 'Fulfilled'
    print('Closing Intent')
    return_object = {
        'sessionState': {
            'activeContexts': active_contexts,
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            "state": "Fulfilled",
            'intent': intent
        },
        #'requestAttributes': {},
        #'messages': messages
    }
    print ("returning:", return_object)
    return return_object
    
def close_and_delegate(active_contexts, session_attributes, intent, messages):
    active_contexts = remove_inactive_context(active_contexts)
    intent['state'] = 'Fulfilled'
    print('Closing Intent')

    return_object = {
        'sessionState': {
            'activeContexts': active_contexts,
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate'
            },
            "state": "Fulfilled",
            'intent': intent
        },
        #'requestAttributes': {},
        #'messages': messages
    }
    print ("returning:", return_object)
    return return_object
    

def elicit_intent(active_contexts, session_attributes, intent, messages):
    intent['state'] = 'Fulfilled'
    active_contexts = remove_inactive_context(active_contexts)
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ElicitIntent'
    session_attributes['previous_slot_to_elicit'] = None
    session_attributes['previous_intent'] = intent['name']
    
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'activeContexts': active_contexts,
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            "state": "Fulfilled"
        },
        'requestAttributes': {},
     'messages': messages
    }

def elicit_slot(slotToElicit, active_contexts, session_attributes, intent, messages):
    intent['state'] = 'InProgress'
    active_contexts = remove_inactive_context(active_contexts)
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ElicitSlot'
    session_attributes['previous_slot_to_elicit'] = slotToElicit
    
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'activeContexts': active_contexts,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slotToElicit
            },
            'intent': intent
        },
        #'requestAttributes': {},
        #'messages': messages
    }

def confirm_intent(active_contexts, session_attributes, intent, messages, **previous_state):
    active_contexts = remove_inactive_context(active_contexts)
    del intent['state']
    if not session_attributes:
        session_attributes = {}
    session_attributes['previous_message'] = json.dumps(messages)
    session_attributes['previous_dialog_action_type'] = 'ConfirmIntent'
    session_attributes['previous_slot_to_elicit'] = None
    if previous_state:
        session_attributes['previous_dialog_action_type'] = previous_state.get('previous_dialog_action_type')
        session_attributes['previous_slot_to_elicit'] = previous_state.get('previous_slot_to_elicit')
    return {
            'sessionState': {
                'activeContexts': active_contexts,
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'ConfirmIntent'
                },
                'intent': intent
            },
            #'requestAttributes': {},
            'messages': messages
        }

def delegate(active_contexts, session_attributes, intent):
    print ('delegate!')
    active_contexts = remove_inactive_context(active_contexts)
    return {
        'sessionState': {
            'activeContexts': active_contexts,
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate'
            },
            'intent': intent,
            'state': 'ReadyForFulfillment'
        },
        #'requestAttributes': {}
    }


def get_intent(intent_request):
    interpretations = intent_request['interpretations'];
    if len(interpretations) > 0:
        return interpretations[0]['intent']
    else:
        return None;

# Look for interpretedValue first. If not go for originalValue
def get_slot(slotname, intent, **kwargs):
    try:
        slot = intent['slots'].get(slotname)
        if not slot:
            return None
        slotvalue = slot.get('value')
        if slotvalue:
            interpretedValue = slotvalue.get('interpretedValue')
            originalValue = slotvalue.get('originalValue')
            if kwargs.get('preference') == 'interpretedValue':
                return interpretedValue
            elif kwargs.get('preference') == 'originalValue':
                return originalValue
            # where there is no preference
            elif interpretedValue:
                return interpretedValue
            else:
                return originalValue
        else:
            return None
    except:
        return None
    
def set_slot(slotname, slotvalue, intent):
    if slotvalue == None:
        intent['slots'][slotname] = None
    else:
        intent['slots'][slotname] = {
                "value": {
                "interpretedValue": slotvalue,
                "originalValue": slotvalue,
                "resolvedValues": [
                    slotvalue
                ]
            }
        }

def get_multi_valued_slot(slotname, intent):
    try:
        values = intent['slots'][slotname]['values']
        if not values:
            return None
        slot_values = [{'interpretedValue':item['value']['interpretedValue'],
                        'originalValue':item['value']['originalValue']}  for item in values]
        return slot_values
    except:
        try:
            return intent['slots'][slotname]['value']['originalValue']
        except:
            return None
            
def get_multi_valued_slot_originalvalue(slotname, intent):
    try:
        values = intent['slots'][slotname]['values']
        if not values:
            return None
        original_slot_values = [item['value']['originalValue'] for item in values]
        return original_slot_values
    except:
        try:
            return intent.get['slots'][slotname]['value']['originalValue']
        except:
            return None

def get_active_contexts(intent_request):
    try:
        return intent_request['sessionState'].get('activeContexts')
    except:
        return []

def get_context_attribute(active_contexts, context_name, attribute_name):
    try:
        context = list(filter(lambda x: x.get('name') == context_name, active_contexts))
        return context[0]['contextAttributes'].get(attribute_name)
    except Exception:
        return None

def get_session_attributes(intent_request):
    try:
        return intent_request['sessionState']['sessionAttributes']
    except:
        return {}

def get_session_attribute(intent_request, session_attribute):
    try:
        return intent_request['sessionState']['sessionAttributes'].get(session_attribute)
    except:
        return None
        
def set_session_attribute(intent_request, session_attribute, value):
    try:
        if intent_request['sessionState'].get('sessionAttributes'):
            intent_request['sessionState']['sessionAttributes'][session_attribute] = value
        else:
            intent_request['sessionState']['sessionAttributes'] = {}
            intent_request['sessionState']['sessionAttributes'][session_attribute] = value
        return intent_request
            
    except:    
        return intent_request

def set_active_contexts(intent_request, context_name, context_attributes, time_to_live, turns_to_live):
    try:
        active_contexts = intent_request.get('sessionState')['activeContexts']
        if not active_contexts:
            intent_request.get('sessionState')['activeContexts'] = []
    except KeyError:
        intent_request.get('sessionState')['activeContexts'] = []
        active_contexts = intent_request.get('sessionState')['activeContexts']
    except Exception:
        return []
    finally:
        active_contexts.append({
            'name': context_name,
            'contextAttributes': context_attributes,
            "timeToLive": {
                "timeToLiveInSeconds": time_to_live,
                "turnsToLive": turns_to_live
            }
        })
        intent_request.get('sessionState')['activeContexts'] = active_contexts

def get_interpreted_intents(intent_request):
    try:
        intents = [{'name':intents_list['intent']['name'], 'nluConfidence':intents_list.get('nluConfidence')}  
                        for intents_list in intent_request['interpretations']]
        return intents
    except:
        return []

def get_previous_slot_to_elicit(intent_request):
    session_attributes = get_session_attributes(intent_request)
    if session_attributes: return session_attributes.get('previous_slot_to_elicit')
    return None
        