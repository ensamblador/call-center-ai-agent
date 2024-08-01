from constructs import Construct
from aws_cdk import ( aws_iam as iam, aws_logs as logs, RemovalPolicy)


class CWLogGroup(Construct):
    def __init__(self, scope: Construct, id: str, log_group_name, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.log_grop  = logs.LogGroup(self, "Log", removal_policy=RemovalPolicy.DESTROY, log_group_name=log_group_name)

