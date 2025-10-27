#!/usr/bin/env python3
import aws_cdk as cdk
import os
from route_optimization_stack import RouteOptimizationStack

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION")
)

RouteOptimizationStack(app, "RouteOptimizationStack", env=env)

app.synth()
