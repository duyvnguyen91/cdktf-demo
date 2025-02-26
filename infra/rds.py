from constructs import Construct
from cdktf import TerraformStack, Token
from imports.aws.provider import AwsProvider
from imports.aws.db_instance import DbInstance
from imports.aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
# from imports.aws.security_group_rule import SecurityGroupRule
from imports.aws.db_subnet_group import DbSubnetGroup
from imports.aws.ssm_parameter import SsmParameter
import random
import string

class RdsStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, vpc_id: str, subnet_ids: list):
        super().__init__(scope, id)
        AwsProvider(self, 'Aws', region='ap-southeast-1')
        # Generate a random password for the RDS instance
        def generate_password(length=16):
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            return "".join(random.choice(chars) for _ in range(length))

        db_password = generate_password()

        # Store password in AWS SSM Parameter Store
        ssm_param = SsmParameter(
            self,
            "db_password",
            name="/cdktf-demo/db-password",
            type="SecureString",
            value=db_password,
        )

        # RDS Security Group
        db_security_group = SecurityGroup(
            self,
            f"{id}-sec-group",
            vpc_id=vpc_id,
            description="Security group for RDS",
            ingress=[SecurityGroupIngress(
                from_port=5432,
                to_port=5432,
                protocol="tcp",
                cidr_blocks=["10.0.0.0/16"]
            )],
            egress=[SecurityGroupEgress(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["10.0.0.0/16"]
            )]
        )

        # Create a DB subnet group
        db_subnet_group = DbSubnetGroup(
            self,
            f"{id}-subnet-group",
            name="demo-db-subnet-group",
            subnet_ids=subnet_ids,
            description="Subnet group for RDS instance",
        )

        # Create the RDS instance
        self.db_instance = DbInstance(
            self,
            id,
            allocated_storage=20,
            instance_class="db.t3.micro",
            engine="postgres",
            engine_version="14",
            username="posgres",
            password=Token.as_string(ssm_param.value),
            db_subnet_group_name=db_subnet_group.name,
            vpc_security_group_ids=[db_security_group.id],
            skip_final_snapshot=True,
            publicly_accessible=False,
        )
