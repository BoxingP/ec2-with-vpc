import os

import boto3
import botocore


class Keypair(object):
    def __init__(self, keypair_name: str, aws_tags: list):
        self.keypair = self.create_keypair(keypair_name, aws_tags)

    @staticmethod
    def create_keypair(keypair_name: str, aws_tags: list):
        try:
            ec2 = boto3.client('ec2')
            response = ec2.describe_key_pairs(KeyNames=[keypair_name])
            return response['KeyPairs'][0].get('KeyName')
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == "InvalidKeyPair.NotFound":
                print("Creating Key Pair...")
                ec2_resource = boto3.resource('ec2')
                keypair = ec2_resource.create_key_pair(
                    KeyName=keypair_name, KeyType='rsa',
                    TagSpecifications=[{'ResourceType': 'key-pair', 'Tags': aws_tags}]
                )
                keypair_path = '/tmp/' + keypair_name + '.pem'
                with open(keypair_path, 'w') as file:
                    file.write(keypair.key_material)
                os.chmod(keypair_path, 0o600)
                print("New Key Pair", keypair_name, "created successfully and is stored in the path:", keypair_path)
                return keypair_name
