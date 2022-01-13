from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    core as cdk
)


class KMSStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, key_name: str, account_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.key = kms.Key(
            self, 'Key',
            alias=key_name,
            description='this key is used to encrypt and decrypt the database backup for rds sql server',
            enabled=True,
            enable_key_rotation=True,
            key_spec=kms.KeySpec.SYMMETRIC_DEFAULT,
            key_usage=kms.KeyUsage.ENCRYPT_DECRYPT,
            pending_window=cdk.Duration.days(30),
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="Enable IAM User Permissions",
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountRootPrincipal()
                        ],
                        actions=[
                            "kms:*"
                        ],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="Allow access for Key Administrators",
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ArnPrincipal(arn='arn:aws-cn:iam::{}:role/ADFS-Admin'.format(account_id))
                        ],
                        actions=[
                            "kms:Create*",
                            "kms:Describe*",
                            "kms:Enable*",
                            "kms:List*",
                            "kms:Put*",
                            "kms:Update*",
                            "kms:Revoke*",
                            "kms:Disable*",
                            "kms:Get*",
                            "kms:Delete*",
                            "kms:TagResource",
                            "kms:UntagResource",
                            "kms:ScheduleKeyDeletion",
                            "kms:CancelKeyDeletion"
                        ],
                        resources=["*"]
                    )
                ]
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        cdk.CfnOutput(
            self, 'OutputKMSKey',
            export_name=construct_id.title().replace('-', '') + 'KeyId',
            value=self.key.key_id
        )
