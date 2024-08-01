import aws_cdk as core
import aws_cdk.assertions as assertions

from call_center_ai_agent.call_center_ai_agent_stack import CallCenterAiAgentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in call_center_ai_agent/call_center_ai_agent_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CallCenterAiAgentStack(app, "call-center-ai-agent")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
