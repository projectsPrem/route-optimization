from aws_cdk import (
    Stack,
    aws_s3_assets as s3_assets,
    aws_elasticbeanstalk as elasticbeanstalk,
    aws_iam as iam,
)
from constructs import Construct

class RouteOptimizationStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 1️⃣ Uploads your Flask app ZIP to S3
        asset = s3_assets.Asset(self, "FlaskAppAsset",
            path="../app.zip"
        )

        # 2️⃣ Creates an Elastic Beanstalk Application
        app = elasticbeanstalk.CfnApplication(self, "FlaskApp",
            application_name="route-optimization-app"
        )

        # 3️⃣ Creates an Application Version linked to the uploaded ZIP
        app_version = elasticbeanstalk.CfnApplicationVersion(self, "AppVersion",
            application_name=app.application_name,
            source_bundle=elasticbeanstalk.CfnApplicationVersion.SourceBundleProperty(
                s3_bucket=asset.s3_bucket_name,
                s3_key=asset.s3_object_key
            )
        )
        app_version.add_dependency(app)

        # 4️⃣ Creates an IAM Role for the EC2 instances in Beanstalk
        role = iam.Role(self, "FlaskEBRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWebTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
            ]
        )

        # 5️⃣ Creates an Elastic Beanstalk Environment (the running app)
        elasticbeanstalk.CfnEnvironment(self, "FlaskEnvironment",
            environment_name="route-optimization-env",
            application_name=app.application_name,
            platform_arn="arn:aws:elasticbeanstalk:ap-south-1::platform/Python 3.12 running on 64bit Amazon Linux 2023/4.7.4",
            option_settings=[
                elasticbeanstalk.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="IamInstanceProfile",
                    value="aws-elasticbeanstalk-ec2-role"
                )
            ],
            version_label=app_version.ref
        )
