#!/usr/bin/env python3
import os

import aws_cdk as cdk

from call_center_ai_agent.call_center_ai_agent_stack import CallCenterAiAgentStack


app = cdk.App()
CallCenterAiAgentStack(app, "CC-Agent")

app.synth()
