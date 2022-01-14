#!/usr/bin/env python3
import datetime
import os

import yaml
from aws_cdk import core as cdk

from stacks.ec2_stack import EC2Stack
from stacks.kms_stack import KMSStack
from stacks.rds_stack import RDSStack
from stacks.s3_bucket_stack import S3BucketStack
from stacks.vpc_stack import VPCStack
from utils.keypair import Keypair

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r', encoding='UTF-8') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
project = config['project'].lower().replace(' ', '-')
environment = config['environment']
vpc_cidr = config['vpc_cidr']
aws_region = config['aws_region']
aws_environment = cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=aws_region)
aws_tags_list = []
for k, v in config['aws_tags'].items():
    aws_tags_list.append({'Key': k, 'Value': v or ' '})

app = cdk.App()
vpc_stack = VPCStack(app, '-'.join([project, environment, 'vpc']), cidr=vpc_cidr, env=aws_environment)
date_now = datetime.datetime.now().strftime("%Y%m%d")
ec2_stack = EC2Stack(app, '-'.join([project, environment, 'ec2']),
                     vpc=vpc_stack.vpc,
                     key_name=Keypair.create_keypair(
                         keypair_name='-'.join([project, environment, date_now, 'key']), aws_tags=aws_tags_list),
                     env=aws_environment)
kms_stack = KMSStack(app, '-'.join([project, environment, 'kms']),
                     key_name='-'.join([project, environment, 'key']),
                     account_id=os.getenv("CDK_DEFAULT_ACCOUNT"),
                     env=aws_environment)
rds_stack = RDSStack(app, '-'.join([project, environment, 'rds']),
                     vpc=vpc_stack.vpc,
                     key=kms_stack.key,
                     rds_name='-'.join([project, environment, 'rds']),
                     env=aws_environment)
s3_bucket_stack = S3BucketStack(app, '-'.join([project, environment, 's3']),
                                bucket_name='-'.join([project, environment, 's3']),
                                env=aws_environment)

for key, value in config['aws_tags'].items():
    cdk.Tags.of(app).add(key, value or " ")
cdk.Tags.of(vpc_stack).add("application", "VPC")
cdk.Tags.of(kms_stack).add("application", "KMS")
cdk.Tags.of(ec2_stack).add("application", "EC2")
cdk.Tags.of(rds_stack).add("application", "RDS")
cdk.Tags.of(s3_bucket_stack).add("application", "S3")
app.synth()
