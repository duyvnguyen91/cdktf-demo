from cdktf import TerraformStack
from constructs import Construct
from imports.vpc import Vpc
from typing import Dict, TypedDict, List, Optional

class Config(TypedDict, total=False):
    azs: List[str]
    cidr: Optional[str]
    publicSubnets: List[str]
    privateSubnets: Optional[List[str]]
    isolatedSubnets: Optional[List[str]]
    singleNatGateway: Optional[bool]
    privateSubnetsTags: Optional[Dict[str, str]]
    publicSubnetsTags: Optional[Dict[str, str]]
    isolatedSubnetsTags: Optional[Dict[str, str]]

class NetworkStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, config: Config):
        super().__init__(scope, id)

        self.vpc = Vpc(
            self,
            id,
            name=id,
            cidr=config.get("cidr", "10.0.0.0/16"),
            azs=config.get("azs", []),
            public_subnets=config.get("publicSubnets", []),
            private_subnets=config.get("privateSubnets", None),
            enable_nat_gateway=config.get("singleNatGateway", True)
        ) 
