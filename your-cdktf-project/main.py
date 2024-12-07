#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.vpc import Vpc
from cdktf_cdktf_provider_aws.subnet import Subnet
from cdktf_cdktf_provider_aws.instance import Instance

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # AWS Provider
        AwsProvider(self, "AWS",
            region="us-west-2"
        )

        # Create VPC
        example_vpc = Vpc(self, "example-vpc",
            cidr_block="10.0.0.0/16",
            tags={
                "Name": "example-vpc",
                "Environment": "dev"
            }
        )

        # Create public subnet
        public_subnet = Subnet(self, "public-subnet",
            vpc_id=example_vpc.id,
            cidr_block="10.0.1.0/24",
            tags={
                "Name": "public-subnet",
                "Environment": "dev"
            }
        )

        # Create EC2 instance
        example_instance = Instance(self, "example-instance",
            ami="ami-0735c191cf914754d",  # Amazon Linux 2 in us-west-2
            instance_type="t2.micro",
            subnet_id=public_subnet.id,
            tags={
                "Name": "example-instance",
                "Environment": "dev"
            }
        )

        # Outputs
        TerraformOutput(self, "vpc_id",
            value=example_vpc.id,
            description="VPC ID"
        )
        
        TerraformOutput(self, "instance_id",
            value=example_instance.id,
            description="EC2 Instance ID"
        )

app = App()
MyStack(app, "example")
app.synth()
