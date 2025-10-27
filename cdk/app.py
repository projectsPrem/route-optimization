#!/usr/bin/env python3
import aws_cdk as cdk
from route_optimization_stack import RouteOptimizationStack

app = cdk.App()

RouteOptimizationStack(
    app, 
    "RouteOptimizationStack",
    env=cdk.Environment(
        account="593793054391",
        region="ap-south-1"
    )
)

app.synth()
