import os

import yaml
from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    core as cdk
)

MSSQL_PORT = 1433


class RDSStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rds_security_group = ec2.SecurityGroup(
            self, 'RDSSecurityGroup', vpc=vpc, description='Security group for rds.',
            security_group_name='-'.join([construct_id, 'rds'.replace(' ', '-')])
        )

        mssql_rds = rds.DatabaseInstance(
            self, 'RDS',
            credentials=rds.Credentials.from_password(
                username='admin',
                password=cdk.SecretValue.secrets_manager(
                    secret_id='prod/ThermoFisherMall/MSSQL',
                    json_field='mysql_password')),
            allocated_storage=450,
            engine=rds.DatabaseInstanceEngine.sql_server_se(
                version=rds.SqlServerEngineVersion.VER_12_00_5571_0_V1
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.MEMORY5,
                ec2.InstanceSize.XLARGE2,
            ),
            license_model=rds.LicenseModel.LICENSE_INCLUDED,
            timezone='China Standard Time',
            copy_tags_to_snapshot=True,
            instance_identifier='-'.join([construct_id, 'rds'.replace(' ', '-')]),
            max_allocated_storage=600,
            multi_az=False,
            port=MSSQL_PORT,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            security_groups=[rds_security_group],
            storage_type=rds.StorageType.GP2,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED)
        )

        with open(os.path.join(os.path.dirname(__file__), 'rds_inbounds.yaml'), 'r', encoding='UTF-8') as file:
            inbounds = yaml.load(file, Loader=yaml.SafeLoader)
        for inbound in inbounds:
            rds_security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(inbound['ip']),
                connection=ec2.Port(
                    protocol=ec2.Protocol.TCP,
                    string_representation=inbound['description'],
                    from_port=MSSQL_PORT,
                    to_port=MSSQL_PORT
                ),
                description=inbound['description']
            )
        rds_security_group.add_ingress_rule(
            peer=ec2.SecurityGroup.from_security_group_id(
                self, "AppSG", security_group_id=cdk.Fn.import_value('AppSecurityGroupId')
            ),
            connection=ec2.Port.tcp(MSSQL_PORT),
            description='from app servers'
        )
