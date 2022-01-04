from aws_cdk import (
    aws_ec2 as ec2,
    core as cdk
)


class VPCStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, cidr: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        public_subnet = ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.PUBLIC, name='Public', cidr_mask=24)
        private_subnet = ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.PRIVATE, name='Private', cidr_mask=24)
        isolated_subnet = ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.ISOLATED, name='Isolated', cidr_mask=24)
        self.vpc = ec2.Vpc(self, 'VPC', cidr=cidr, max_azs=2,
                           enable_dns_hostnames=True, enable_dns_support=True,
                           subnet_configuration=[public_subnet, private_subnet, isolated_subnet]
                           )

        cdk.CfnOutput(self, 'OutputVPC', export_name=construct_id.title().replace('-', ''), value=self.vpc.vpc_id)
