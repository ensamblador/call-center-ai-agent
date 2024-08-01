from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput
)
from constructs import Construct
from aws_cdk.aws_s3_assets import Asset
from bots import LexBotV2
from lambdas import Lambdas
from databases import Tables

class CallCenterAiAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        Tb = Tables(self, 'Tb')
        Fn  = Lambdas(self,'Fn')

        Fn.fulfillment.add_environment("CONVERSATION_TABLE_NAME", Tb.conversationHistory.table_name)
        Fn.fulfillment.add_environment("ORDER_TABLE_NAME", Tb.pedidos.table_name)


        self.asset = Asset(self, "Zipped", path="bots/pedido-llm")
        bot_locale = "es_419"
        bot_name="demo-llm" 

        demo_bot = LexBotV2(self, "BotDemo", 
                            bot_name=bot_name, 
                            bot_locale = bot_locale,
                            code_hook= Fn.fulfillment, 
                            s3_key=self.asset.s3_object_key, s3_bucket= self.asset.bucket) 



