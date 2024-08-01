from email import policy
from constructs import Construct
from aws_cdk import ( aws_iam as iam, Stack)


BOT_NAME = 'Agendar-v2'
DATA_PRIVACY = {'ChildDirected': False}
SENTIMENT_ANALYSYS_SETTINGS = {'DetectSentiment': False}
IDLE_SESION_TIMEOUT_IN_SECONDS = 120


class LexV2Role(Construct):
    def __init__(self, scope: Construct, id: str, bot_name, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        crea_rol = True
        stk = Stack.of(self)
        account_id = stk.account
        
        # if crea_rol = False, put the actual role name to be used below
        role_name = f"AWSServiceRoleForLexV2Bots_{bot_name}"

        if crea_rol:
            self.arn = f'arn:aws:iam::{account_id}:role/aws-service-role/lexv2.amazonaws.com/{role_name}'
            bot_role = iam.CfnServiceLinkedRole( self, 'R',
                aws_service_name='lexv2.amazonaws.com',
                custom_suffix=bot_name,
            )
            self.role = bot_role
            if SENTIMENT_ANALYSYS_SETTINGS['DetectSentiment'] == True:

                policy = iam.Policy(self, "comprehend",statements=[
                    iam.PolicyStatement(actions=["Comprehend:*"], resources=['*'])]
                )
                bot_role.attach_inline_policy(policy=policy)


        
        else:

            iam.Role.from_role_arn(self, "rol", self.arn).attach_inline_policy(policy=policy)
            bot_role = iam.Role.from_role_name(self, 'SLRExistente', role_name=role_name)
            self.role = bot_role


        