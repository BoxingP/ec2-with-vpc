#!/usr/bin/env python3
import datetime
import os

import yaml
from aws_cdk import core as cdk

from ec2_with_vpc.ec2_stack import EC2Stack
from ec2_with_vpc.rds_stack import RDSStack
from ec2_with_vpc.s3_bucket_stack import S3BucketStack
from ec2_with_vpc.vpc_stack import VPCStack
from utils.keypair import Keypair

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r', encoding='UTF-8') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
project = config['project'].lower().replace(' ', '-')
environment = config['environment']
aws_tags_list = []
for k, v in config['aws_tags'].items():
    aws_tags_list.append({'Key': k, 'Value': v or ' '})

app = cdk.App()
vpc_stack = VPCStack(app, '-'.join([project, environment, 'vpc']),
                     env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                         region=os.getenv("CDK_DEFAULT_REGION")))
date_now = datetime.datetime.now().strftime("%Y%m%d")
ec2_stack = EC2Stack(app, '-'.join([project, environment, 'ec2']),
                     vpc=vpc_stack.vpc,
                     key_name=Keypair.create_keypair(
                         keypair_name='-'.join([project, environment, date_now, 'key']), aws_tags=aws_tags_list),
                     env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                         region=os.getenv("CDK_DEFAULT_REGION")))
rds_stack = RDSStack(app, '-'.join([project, environment, 'rds']),
                     vpc=vpc_stack.vpc,
                     env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                         region=os.getenv("CDK_DEFAULT_REGION")))
s3_bucket_stack = S3BucketStack(app, '-'.join([project, environment, 's3']),
                                env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                                    region=os.getenv("CDK_DEFAULT_REGION")))

for key, value in config['aws_tags'].items():
    cdk.Tags.of(app).add(key, value or " ")
cdk.Tags.of(vpc_stack).add("application", "VPC")
cdk.Tags.of(ec2_stack).add("application", "EC2")
cdk.Tags.of(rds_stack).add("application", "RDS")
app.synth()
