import os

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core as cdk
)

OFFICE_IP = '222.126.242.202'
HTTPS_PORT = 443
MSSQL_PORT = 1433
RDP_PORT = 3389


class EC2Stack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, key_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_windows_image = ec2.MachineImage.generic_windows(
            ami_map={os.getenv('AWS_DEFAULT_REGION'): 'ami-0b50407ec100af505'})
        db_windows_image = ec2.MachineImage.generic_windows(
            ami_map={os.getenv('AWS_DEFAULT_REGION'): 'ami-0cfa71f4e607f9c31'})
        app_security_group = ec2.SecurityGroup(self, 'AppSecurityGroup', vpc=vpc,
                                               description='Security group for app servers.',
                                               security_group_name='-'.join([construct_id, 'app sg'.replace(' ', '-')])
                                               )
        db_security_group = ec2.SecurityGroup(self, 'DBSecurityGroup', vpc=vpc,
                                              description='Security group for db servers.',
                                              security_group_name='-'.join([construct_id, 'db sg'.replace(' ', '-')])
                                              )
        app_role = iam.Role(self, 'AppRole',
                            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com.cn'),
                            description="IAM role for app servers",
                            managed_policies=[],
                            role_name='-'.join([construct_id, 'app servers'.replace(' ', '-')]),
                            )
        db_role = iam.Role(self, 'DBRole',
                           assumed_by=iam.ServicePrincipal('ec2.amazonaws.com.cn'),
                           description="IAM role for db servers",
                           managed_policies=[],
                           role_name='-'.join([construct_id, 'db servers'.replace(' ', '-')]),
                           )

        app_instance = ec2.Instance(self, 'AppEC2',
                                    instance_type=ec2.InstanceType('t2.xlarge'),
                                    machine_image=app_windows_image,
                                    vpc=vpc,
                                    block_devices=[
                                        ec2.BlockDevice(
                                            device_name='/dev/sda1',
                                            volume=ec2.BlockDeviceVolume.ebs(
                                                volume_size=200,
                                                encrypted=False,
                                                delete_on_termination=True,
                                                volume_type=ec2.EbsDeviceVolumeType.GP2
                                            )
                                        )
                                    ],
                                    instance_name='-'.join([construct_id, 'app'.replace(' ', '-')]),
                                    key_name=key_name,
                                    role=app_role,
                                    security_group=app_security_group,
                                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
                                    )
        db_instance = ec2.Instance(self, 'DBEC2',
                                   instance_type=ec2.InstanceType('t2.xlarge'),
                                   machine_image=db_windows_image,
                                   vpc=vpc,
                                   block_devices=[
                                       ec2.BlockDevice(
                                           device_name='/dev/sda1',
                                           volume=ec2.BlockDeviceVolume.ebs(
                                               volume_size=200,
                                               encrypted=False,
                                               delete_on_termination=True,
                                               volume_type=ec2.EbsDeviceVolumeType.GP2
                                           )
                                       )
                                   ],
                                   instance_name='-'.join([construct_id, 'db'.replace(' ', '-')]),
                                   key_name=key_name,
                                   role=db_role,
                                   security_group=db_security_group,
                                   vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)
                                   )
        eip = ec2.CfnEIP(self, 'AppInstanceIP', domain=vpc.vpc_id, instance_id=app_instance.instance_id,
                         tags=[
                             cdk.CfnTag(key='Name', value='-'.join([construct_id, 'app server eip'.replace(' ', '-')]))
                         ]
                         )

        app_security_group.add_ingress_rule(peer=ec2.Peer.ipv4(OFFICE_IP + '/32'),
                                            connection=ec2.Port(protocol=ec2.Protocol.TCP,
                                                                string_representation="from office",
                                                                from_port=HTTPS_PORT,
                                                                to_port=HTTPS_PORT),
                                            description='from office')
        app_security_group.add_ingress_rule(peer=ec2.Peer.ipv4(OFFICE_IP + '/32'),
                                            connection=ec2.Port(protocol=ec2.Protocol.TCP,
                                                                string_representation="from office",
                                                                from_port=RDP_PORT,
                                                                to_port=RDP_PORT),
                                            description='from office')
        db_security_group.add_ingress_rule(peer=ec2.Peer.ipv4(app_instance.instance_public_ip + '/32'),
                                           connection=ec2.Port(protocol=ec2.Protocol.TCP,
                                                               string_representation="from app",
                                                               from_port=MSSQL_PORT,
                                                               to_port=MSSQL_PORT),
                                           description='from app servers')
        db_security_group.connections.allow_from(app_security_group, ec2.Port.tcp(MSSQL_PORT), "from app servers")
        db_security_group.connections.allow_from(app_security_group, ec2.Port.tcp(RDP_PORT), "from app servers")

        cdk.CfnOutput(self, 'OutputAppInstanceId', export_name='AppInstanceId', value=app_instance.instance_id)
        cdk.CfnOutput(self, 'OutputAppPublicIP', export_name='AppPublicIP', value=app_instance.instance_public_ip)
        cdk.CfnOutput(self, 'OutputDBInstanceId', export_name='DBInstanceId', value=db_instance.instance_id)
