from enum import Enum

from aws_cdk import aws_ec2 as ec2


class InstanceClass(Enum):
    t2 = ec2.InstanceClass.BURSTABLE2
    m4 = ec2.InstanceClass.STANDARD4
    m5 = ec2.InstanceClass.STANDARD5


class InstanceSize(Enum):
    nano = ec2.InstanceSize.NANO
    micro = ec2.InstanceSize.MICRO
    small = ec2.InstanceSize.SMALL
    medium = ec2.InstanceSize.MEDIUM
    large = ec2.InstanceSize.LARGE
    xlarge = ec2.InstanceSize.XLARGE
    xlarge2 = ec2.InstanceSize.XLARGE2
    xlarge3 = ec2.InstanceSize.XLARGE3
    xlarge4 = ec2.InstanceSize.XLARGE4
    xlarge8 = ec2.InstanceSize.XLARGE8
    metal = ec2.InstanceSize.METAL


class RDSInstanceType(object):

    def get_instance_type(self, type_str: str):
        class_str, size_str = type_str.split('.')
        instance_class = InstanceClass[class_str].value
        instance_size = InstanceSize[self.format(size_str)].value
        return ec2.InstanceType.of(instance_class, instance_size)

    @staticmethod
    def format(string):
        if string[0].isdigit():
            return string[1:] + string[0]
        else:
            return string
