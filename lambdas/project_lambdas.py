import sys

from aws_cdk import (aws_lambda, Duration, aws_iam as iam)

from constructs import Construct


LAMBDA_TIMEOUT= 30

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    memory_size=256,
    architecture=aws_lambda.Architecture.ARM_64,
    runtime=aws_lambda.Runtime.PYTHON_3_12,

    tracing= aws_lambda.Tracing.ACTIVE)


from layers.all_layers.project_layers import Boto3


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        COMMON_LAMBDA_CONF = dict(environment= {},**BASE_LAMBDA_CONFIG)

        boto3_later = Boto3(self, "B3")

        self.fulfillment = aws_lambda.Function(
            self, "LexFullfillment", 
            function_name="Pedido-Fulfilment", handler="lambda_function.lambda_handler",
             layers=[boto3_later.layer],
            code = aws_lambda.Code.from_asset("./lambdas/code/fulfillment"), **COMMON_LAMBDA_CONF)
        


        """
        self.async_llm_call = aws_lambda.Function(
            self, "AsyncLMLCall", 
            function_name="Async-LLM-Call",
            handler="lambda_function.lambda_handler",
            layers=[boto3_later.layer],
            code = aws_lambda.Code.from_asset("./lambdas/code/async_llm_call"), **COMMON_LAMBDA_CONF)
        
        self.async_llm_call.grant_invoke(self.fulfillment)

        """
        self.get_customer_data = aws_lambda.Function(
            self, "GCD", 
            function_name="Get-Customer-Data",
            handler="lambda_function.lambda_handler",
            code = aws_lambda.Code.from_asset("./lambdas/code/get_customer_data"), **COMMON_LAMBDA_CONF)
        

        self.fulfillment.add_to_role_policy(iam.PolicyStatement(actions=['dynamodb:*'],resources=["*"]))
        self.fulfillment.add_to_role_policy(iam.PolicyStatement(actions=['bedrock:*'],resources=["*"]))

        self.get_customer_data.add_to_role_policy(iam.PolicyStatement(actions=['dynamodb:*'], resources=["*"]))

