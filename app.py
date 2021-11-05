#!/usr/bin/env python3
import datetime
import os

import boto3
import botocore
import yaml

from aws_cdk import core as cdk
from ec2_with_vpc.vpc_stack import VPCStack
from ec2_with_vpc.ec2_stack import EC2Stack

with open('aws_tags.yaml', 'r', encoding='UTF-8') as file:
    aws_tags = yaml.load(file, Loader=yaml.SafeLoader)
project = aws_tags['project'].lower().replace(' ', '-')
environment = aws_tags['environment']
aws_tags_list = []
for k, v in aws_tags.items():
    aws_tags_list.append({'Key': k, 'Value': v or ' '})

date_now = datetime.datetime.now().strftime("%Y%m%d")
keypair_name = '-'.join([project, environment, date_now, 'key'])
try:
    ec2 = boto3.client('ec2')
    response = ec2.describe_key_pairs(KeyNames=[keypair_name])
except botocore.exceptions.ClientError as error:
    if error.response['Error']['Code'] == "InvalidKeyPair.NotFound":
        print("Creating Key Pair...")
        ec2_resource = boto3.resource('ec2')
        keypair = ec2_resource.create_key_pair(KeyName=keypair_name, KeyType='rsa',
                                               TagSpecifications=[{'ResourceType': 'key-pair', 'Tags': aws_tags_list}])
        keypair_path = '/tmp/' + keypair_name + '.pem'
        with open(keypair_path, 'w') as file:
            file.write(keypair.key_material)
        print("New Key Pair", keypair_name, "created successfully and is stored in the path:", keypair_path)

app = cdk.App()
vpc_stack = VPCStack(app, '-'.join([project, environment, 'vpc']),
                     env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                         region=os.getenv("CDK_DEFAULT_REGION")))
ec2_stack = EC2Stack(app, '-'.join([project, environment, 'ec2']), vpc=vpc_stack.vpc, key_name=keypair_name,
                     env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                                         region=os.getenv("CDK_DEFAULT_REGION")))

for key, value in aws_tags.items():
    cdk.Tags.of(app).add(key, value or " ")
cdk.Tags.of(vpc_stack).add("application", "VPC")
cdk.Tags.of(ec2_stack).add("application", "EC2")
app.synth()
