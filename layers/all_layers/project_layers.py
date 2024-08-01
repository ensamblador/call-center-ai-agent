from constructs import Construct

from aws_cdk import (
    aws_lambda as _lambda

)



class Boto3(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        boto3_layer = _lambda.LayerVersion(
            self, "boto3", code=_lambda.Code.from_asset("./layers/all_layers/boto3.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_10, _lambda.Runtime.PYTHON_3_11, _lambda.Runtime.PYTHON_3_9, _lambda.Runtime.PYTHON_3_12 ])

        
        self.layer = boto3_layer

