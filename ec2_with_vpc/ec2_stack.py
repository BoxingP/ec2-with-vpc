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
        s3_bucket_name = cdk.Fn.import_value(
            construct_id.rsplit('-', 1)[0].title().replace('-', '') + 'S3BucketName'
        )
        with open(os.path.join(os.path.dirname(__file__), 'ec2_config.yaml'), 'r', encoding='UTF-8') as file:
            ec2_config = yaml.load(file, Loader=yaml.SafeLoader)

        app_windows_image = ec2.MachineImage.generic_windows(
            ami_map={os.getenv('AWS_DEFAULT_REGION'): ec2_config['ami']})
        app_security_group = ec2.SecurityGroup(self, 'AppSecurityGroup', vpc=vpc,
                                               description='Security group for app servers.',
                                               security_group_name='-'.join([construct_id, 'app sg'.replace(' ', '-')])
                                               )
        operating_s3_policy = iam.ManagedPolicy(
            self, 'OperatingS3Policy',
            managed_policy_name='-'.join(
                [construct_id, 'operating s3 policy'.replace(' ', '-')]
            ),
            description='Policy to operate S3 bucket',
            statements=[
                iam.PolicyStatement(
                    sid='AllowListOfSpecificBucket',
                    actions=['s3:ListBucket'],
                    resources=[
                        'arn:aws-cn:s3:::' + s3_bucket_name,
                        'arn:aws-cn:s3:::' + s3_bucket_name + '/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid='AllowGetObjectOfSpecificBucket',
                    actions=['s3:GetObject'],
                    resources=[
                        'arn:aws-cn:s3:::' + s3_bucket_name,
                        'arn:aws-cn:s3:::' + s3_bucket_name + '/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid='AllowPutObjectOfSpecificBucket',
                    actions=['s3:PutObject'],
                    resources=[
                        'arn:aws-cn:s3:::' + s3_bucket_name,
                        'arn:aws-cn:s3:::' + s3_bucket_name + '/*'
                    ]
                )
            ]
        )
        app_role = iam.Role(self, 'AppRole',
                            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com.cn'),
                            description="IAM role for app servers",
                            managed_policies=[operating_s3_policy],
                            role_name='-'.join([construct_id, 'app servers'.replace(' ', '-')]),
                            )
        block_devices = []
        for device in ec2_config['block_devices']:
            block_devices.append(
                ec2.BlockDevice(
                    device_name=device['name'],
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=int(device['size']),
                        encrypted=False,
                        delete_on_termination=True,
                        volume_type=ec2.EbsDeviceVolumeType.GP2
                    )
                )
            )

        app_instance = ec2.Instance(self, 'AppEC2',
                                    instance_type=ec2.InstanceType(ec2_config['type']),
                                    machine_image=app_windows_image,
                                    vpc=vpc,
                                    block_devices=block_devices,
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

        for inbound in ec2_config['inbounds']:
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

        cdk.CfnOutput(
            self, 'OutputAppInstanceId',
            export_name=construct_id.title().replace('-', '') + 'InstanceId', value=app_instance.instance_id)
        cdk.CfnOutput(
            self, 'OutputAppPublicIP',
            export_name=construct_id.title().replace('-', '') + 'InstancePublicIP',
            value=app_instance.instance_public_ip)
        cdk.CfnOutput(
            self, 'OutputAppSecurityGroupId',
            export_name=construct_id.title().replace('-', '') + 'SecurityGroupId',
            value=app_security_group.security_group_id)
