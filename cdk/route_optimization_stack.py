from aws_cdk import (
    Stack,
    aws_s3_assets as s3_assets,
    aws_elasticbeanstalk as elasticbeanstalk,
    aws_iam as iam,
)
from constructs import Construct

class RouteOptimizationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Upload Flask app zip to S3
        app_zip_asset = s3_assets.Asset(self, "FlaskAppZip", path="../app.zip")

        # Beanstalk Application
        app = elasticbeanstalk.CfnApplication(
            self, "FlaskApp", application_name="route-optimization-app"
        )

        # IAM Role
        role = iam.Role(
            self,
            "FlaskEBRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWebTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        # Use the correct Platform ARN for your region
        platform_arn = "arn:aws:elasticbeanstalk:ap-south-1::platform/Python 3.9 running on 64bit Amazon Linux 2023/4.7.4"

        # Environment
        elasticbeanstalk.CfnEnvironment(
            self,
            "FlaskEnvironment",
            environment_name="route-optimization-env",
            application_name=app.application_name,
            platform_arn=platform_arn,
            version_label="v1",
            option_settings=[
                elasticbeanstalk.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="IamInstanceProfile",
                    value="aws-elasticbeanstalk-ec2-role",
                ),
            ],
        )
