from constructs import Construct
from aws_cdk import ( aws_iam as iam,aws_s3_deployment as s3deploy, aws_s3 as s3, RemovalPolicy)


class S3BotFiles(Construct):
    def __init__(self, scope: Construct, id: str, bot_location, s3_bucket = None,  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        if s3_bucket == None:
            self.bucket = s3.Bucket(self, "S3", removal_policy=RemovalPolicy.DESTROY)
        else:
            self.bucket = s3_bucket

        self.s3deploy = s3deploy.BucketDeployment(self, "B",
            sources=[s3deploy.Source.asset(bot_location)],
            destination_bucket = self.bucket,
            destination_key_prefix="bot_files"
        )
        


