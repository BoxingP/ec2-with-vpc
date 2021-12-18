import os

import yaml
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core as cdk
)


class EC2Stack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, vpc: ec2.Vpc, key_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_windows_image = ec2.MachineImage.generic_windows(
            ami_map={os.getenv('AWS_DEFAULT_REGION'): 'ami-0ace3d6977b9072ee'})
        app_security_group = ec2.SecurityGroup(self, 'AppSecurityGroup', vpc=vpc,
                                               description='Security group for app servers.',
                                               security_group_name='-'.join([construct_id, 'app sg'.replace(' ', '-')])
                                               )
        app_role = iam.Role(self, 'AppRole',
                            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com.cn'),
                            description="IAM role for app servers",
                            managed_policies=[],
                            role_name='-'.join([construct_id, 'app servers'.replace(' ', '-')]),
                            )

        app_instance = ec2.Instance(self, 'AppEC2',
                                    instance_type=ec2.InstanceType('t2.xlarge'),
                                    machine_image=app_windows_image,
                                    vpc=vpc,
                                    block_devices=[
                                        ec2.BlockDevice(
                                            device_name='/dev/sda1',
                                            volume=ec2.BlockDeviceVolume.ebs(
                                                volume_size=30,
                                                encrypted=False,
                                                delete_on_termination=True,
                                                volume_type=ec2.EbsDeviceVolumeType.GP2
                                            )
                                        ),
                                        ec2.BlockDevice(
                                            device_name='xvdf',
                                            volume=ec2.BlockDeviceVolume.ebs(
                                                volume_size=1400,
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
        eip = ec2.CfnEIP(self, 'AppInstanceIP', domain=vpc.vpc_id, instance_id=app_instance.instance_id,
                         tags=[
                             cdk.CfnTag(key='Name', value='-'.join([construct_id, 'app server eip'.replace(' ', '-')]))
                         ]
                         )

        with open(os.path.join(os.path.dirname(__file__), 'ec2_inbounds.yaml'), 'r', encoding='UTF-8') as file:
            inbounds = yaml.load(file, Loader=yaml.SafeLoader)
        for inbound in inbounds:
            for port in inbound['port']:
                if '-' in str(port):
                    [from_port, to_port] = str(port).split('-')
                else:
                    from_port = port
                    to_port = port
                app_security_group.add_ingress_rule(
                    peer=ec2.Peer.ipv4(inbound['ip']),
                    connection=ec2.Port(
                        protocol=ec2.Protocol.TCP,
                        string_representation=inbound['description'],
                        from_port=int(from_port),
                        to_port=int(to_port)
                    ),
                    description=inbound['description']
                )

        cdk.CfnOutput(self, 'OutputAppInstanceId', export_name='AppInstanceId', value=app_instance.instance_id)
        cdk.CfnOutput(self, 'OutputAppPublicIP', export_name='AppPublicIP', value=app_instance.instance_public_ip)
        cdk.CfnOutput(self, 'OutputAppSecurityGroupId', export_name='AppSecurityGroupId', value=app_security_group.security_group_id)
