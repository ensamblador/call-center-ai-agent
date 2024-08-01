#!/usr/bin/env python3
import os

import aws_cdk as cdk

from layers.layers_stack import LayersStack

TAGS = {"app": "whatsapp-ia", "customer": "layer"}

app = cdk.App()
stk = LayersStack(app, "LAYER")
if TAGS.keys():
    for k in TAGS.keys():
        cdk.Tags.of(stk).add(k, TAGS[k])
app.synth()
