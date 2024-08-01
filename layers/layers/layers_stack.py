import sys
from aws_cdk import (
    # Duration,
    Stack,
    aws_ssm as ssm
)
from constructs import Construct

from all_layers import BS4Request,LangchainLayer, YoutubeApi, Xray, Common

sys.path.append("..")
import config

class LayersStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        BS = BS4Request(self, "BS4")
        LC = LangchainLayer(self, "LanchainLayer")
        YT = YoutubeApi(self, "YoutubeApi")
        XR = Xray(self, "Xray")
        Com = Common(self, "Common")


        ssm.StringParameter( self, "xray_layer",parameter_name=config.XRAY_LAYER_PARAM, string_value=XR.layer.layer_version_arn)   
        ssm.StringParameter( self, "requests_layer",parameter_name=config.REQUESTS_LAYER_PARAM, string_value=BS.layer.layer_version_arn)   
        ssm.StringParameter( self, "langchain_layer",parameter_name=config.LANGCHAIN_LAYER_PARAM, string_value=LC.layer.layer_version_arn)   
        ssm.StringParameter( self, "youtube_layer",parameter_name=config.YOUTUBE_LAYER_PARAM, string_value=YT.layer.layer_version_arn)   
        ssm.StringParameter( self, "common_layer",parameter_name=config.COMMON_LAYER_PARAM, string_value=Com.layer.layer_version_arn)   

