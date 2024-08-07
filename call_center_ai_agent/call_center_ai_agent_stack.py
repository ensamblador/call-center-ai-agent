from aws_cdk import (
    Stack,aws_lambda, aws_iam as iam
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
        Fn.fulfillment.add_environment("TICKET_TABLE_NAME", Tb.issues.table_name)
        Fn.get_customer_data.add_environment("ORDER_TABLE_NAME", Tb.pedidos.table_name)

        alias_name = None #"production"
        bot_name="demo-llm" 

        if alias_name:
            alias = aws_lambda.Alias(
                self, "LambdaAlias",
                alias_name=alias_name,
                version=Fn.fulfillment.current_version,
                provisioned_concurrent_executions=2
            )
            alias.add_permission(
                principal=iam.ServicePrincipal("lexv2.amazonaws.com"),id=f"{bot_name}-invoke",
                action='lambda:InvokeFunction', source_arn = f"arn:aws:lex:{Stack.of(self).region}:{Stack.of(self).account}:bot-alias/*")
            
        else:
            Fn.fulfillment.add_permission(
                principal=iam.ServicePrincipal("lexv2.amazonaws.com"),id=f"{bot_name}-invoke",
                action='lambda:InvokeFunction', source_arn = f"arn:aws:lex:{Stack.of(self).region}:{Stack.of(self).account}:bot-alias/*")
            



        self.asset = Asset(self, "Zipped", path="bots/pedido-llm")
        bot_locale = "es_419"

        demo_bot = LexBotV2(self, "BotDemo", 
                            bot_name=bot_name, 
                            bot_locale = bot_locale,
                            code_hook= Fn.fulfillment, 
                            alias=alias_name,
                            s3_key=self.asset.s3_object_key, s3_bucket= self.asset.bucket) 



