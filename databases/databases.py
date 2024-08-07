from aws_cdk import RemovalPolicy, custom_resources as cr, aws_dynamodb as ddb, CfnOutput
from constructs import Construct
import json




REMOVAL_POLICY = RemovalPolicy.DESTROY

TABLE_CONFIG = dict(
    removal_policy=REMOVAL_POLICY, billing_mode=ddb.BillingMode.PAY_PER_REQUEST
)


class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.conversationHistory = ddb.Table(
            self,
            "ConversationHistory",
            partition_key=ddb.Attribute(
                name="sessionId", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )

        self.issues = ddb.Table(
            self,
            "issue",
            partition_key=ddb.Attribute(
                name="issue_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )


        self.pedidos = ddb.Table(
            self,
            "orders",
            partition_key=ddb.Attribute(
                name="order_number", type=ddb.AttributeType.STRING
            ),
            **TABLE_CONFIG,
        )

        self.pedidos.add_global_secondary_index(
            index_name="phone_number",
            partition_key=ddb.Attribute(
                name="phone_number", type=ddb.AttributeType.STRING
            ),
        )

        #Load table with sample data

        with open("databases/orders.json") as f:
            sample_data = json.load(f)

        parameters = {
            "RequestItems": {
                self.pedidos.table_name: [
                    {"PutRequest": {"Item": item}}
                    for item in sample_data.get("Items")
                ]
            }
        }

        cr.AwsCustomResource(
            self,
            "BatchWriteItem",
            on_update=cr.AwsSdkCall( 
                service="dynamodb",
                action="BatchWriteItem",
                parameters=parameters,
                physical_resource_id=cr.PhysicalResourceId.of(f"BatchWriteItem-{self.pedidos.table_name}"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )


        CfnOutput(self, "SampleData", value=json.dumps(sample_data))