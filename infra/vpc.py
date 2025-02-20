from cdktf import TerraformStack
from constructs import Construct
from imports.aws import Vpc, Subnet

class VPCStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        self.vpc = Vpc(self, "VPC", cidr_block="10.0.0.0/16")
        self.subnet = Subnet(self, "Subnet", vpc_id=self.vpc.id, cidr_block="10.0.1.0/24")
