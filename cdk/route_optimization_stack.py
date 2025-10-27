import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_elasticbeanstalk as elasticbeanstalk,
)

class RouteOptimizationStack(cdk.Stack):

    def __init__(self, scope: cdk.App, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 🪣 Create an S3 bucket to hold app.zip
        bucket = s3.Bucket(
            self, "FlaskAppBucket",
            versioned=False,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # 🧠 Create Elastic Beanstalk Application
        app = elasticbeanstalk.CfnApplication(
            self, "FlaskApplication",
            application_name="route-optimization"
        )

        # 📦 Upload app.zip manually or through GitHub Actions before deploy
        app_version = elasticbeanstalk.CfnApplicationVersion(
            self, "AppVersion",
            application_name=app.application_name,
            source_bundle=elasticbeanstalk.CfnApplicationVersion.SourceBundleProperty(
                s3_bucket=bucket.bucket_name,
                s3_key="app.zip"
            )
        )

        app_version.add_dependency(app)

        # 🌍 Elastic Beanstalk Environment (Stable Python version)
        env = elasticbeanstalk.CfnEnvironment(
            self, "FlaskEnvironment",
            environment_name="route-optimization-env",
            application_name=app.application_name,
            solution_stack_name="64bit Amazon Linux 2 v3.5.5 running Python 3.9",
            version_label=app_version.ref
        )
