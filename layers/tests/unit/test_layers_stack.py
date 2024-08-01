import aws_cdk as core
import aws_cdk.assertions as assertions

from layers.layers_stack import LayersStack

# example tests. To run these tests, uncomment this file along with the example
# resource in layers/layers_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LayersStack(app, "layers")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
