import os

import yaml
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    core as cdk
)


class RDSStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rds_security_group = ec2.SecurityGroup(
            self, 'RDSSecurityGroup', vpc=vpc, description='Security group for rds.',
            security_group_name='-'.join([construct_id, 'rds'.replace(' ', '-')])
        )
        with open(os.path.join(os.path.dirname(__file__), 'rds_config.yaml'), 'r', encoding='UTF-8') as file:
            rds_config = yaml.load(file, Loader=yaml.SafeLoader)
            rds_port = rds_config['rds_port']
        for inbound in rds_config['inbounds']:
            rds_security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(inbound['ip']),
                connection=ec2.Port(
                    protocol=ec2.Protocol.TCP,
                    string_representation=inbound['description'],
                    from_port=rds_port,
                    to_port=rds_port
                ),
                description=inbound['description']
            )
        rds_security_group.add_ingress_rule(
            peer=ec2.SecurityGroup.from_security_group_id(
                self, "AppSG",
                security_group_id=cdk.Fn.import_value(
                    construct_id.rsplit('-', 1)[0].title().replace('-', '') + 'Ec2SecurityGroupId'
                )
            ),
            connection=ec2.Port.tcp(rds_port),
            description='from app servers'
        )

        s3_bucket_name = cdk.Fn.import_value(
            construct_id.rsplit('-', 1)[0].title().replace('-', '') + 'S3BucketName'
        )
        backup_restore_from_s3_policy = iam.ManagedPolicy(
            self, 'BackupRestoreFromS3Policy',
            managed_policy_name='-'.join(
                [construct_id, 'backup restore from s3 policy'.replace(' ', '-')]
            ),
            description='Policy to backup and restore from S3 bucket',
            statements=[
                iam.PolicyStatement(
                    sid='AllowListOfSpecificBucket',
                    actions=['s3:ListBucket', 's3:GetBucketLocation'],
                    resources=[
                        'arn:aws-cn:s3:::' + s3_bucket_name
                    ]
                ),
                iam.PolicyStatement(
                    sid='AllowGetPutObjectOfSpecificBucket',
                    actions=['s3:GetObject', 's3:PutObject', 's3:ListMultipartUploadParts', 's3:AbortMultipartUpload'],
                    resources=[
                        'arn:aws-cn:s3:::' + s3_bucket_name + '/*'
                    ]
                )
            ]
        )
        rds_role = iam.Role(
            self, 'RDSRole',
            assumed_by=iam.ServicePrincipal('rds.amazonaws.com'),
            description="IAM role for rds",
            managed_policies=[backup_restore_from_s3_policy],
            role_name='-'.join([construct_id, 'rds'.replace(' ', '-')]),
        )
        option_group = rds.OptionGroup(
            self, 'OptionGroup',
            engine=rds.DatabaseInstanceEngine.sql_server_ee(
                version=rds.SqlServerEngineVersion.VER_12_00_5571_0_V1
            ),
            configurations=[
                rds.OptionConfiguration(
                    name='SQLSERVER_BACKUP_RESTORE',
                    settings={'IAM_ROLE_ARN': rds_role.role_arn}
                )
            ]
        )

        mssql_rds = rds.DatabaseInstance(
            self, 'RDS',
            character_set_name='Chinese_PRC_CI_AS',
            credentials=rds.Credentials.from_password(
                username='admin',
                password=cdk.SecretValue.secrets_manager(
                    secret_id='prod/ThermoFisherMall/MSSQL',
                    json_field='mssql_password')),
            allocated_storage=130,
            engine=rds.DatabaseInstanceEngine.sql_server_ee(
                version=rds.SqlServerEngineVersion.VER_12_00_5571_0_V1
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.STANDARD5,
                ec2.InstanceSize.XLARGE2,
            ),
            license_model=rds.LicenseModel.LICENSE_INCLUDED,
            timezone='China Standard Time',
            auto_minor_version_upgrade=False,
            backup_retention=cdk.Duration.days(7),
            cloudwatch_logs_exports=['error'],
            copy_tags_to_snapshot=True,
            delete_automated_backups=True,
            deletion_protection=False,
            instance_identifier='-'.join([construct_id, 'rds'.replace(' ', '-')]),
            max_allocated_storage=600,
            multi_az=False,
            option_group=option_group,
            port=rds_port,
            preferred_backup_window='19:00-19:30',
            publicly_accessible=False,
            removal_policy=cdk.RemovalPolicy.SNAPSHOT,
            security_groups=[rds_security_group],
            storage_type=rds.StorageType.GP2,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED)
        )

        cdk.CfnOutput(
            self, 'OutputRDSEndpointAddress',
            export_name=construct_id.title().replace('-', '') + 'EndpointAddress',
            value=mssql_rds.db_instance_endpoint_address
        )
        cdk.CfnOutput(
            self, 'OutputRDSEndpointPort',
            export_name=construct_id.title().replace('-', '') + 'EndpointPort',
            value=mssql_rds.db_instance_endpoint_port
        )
