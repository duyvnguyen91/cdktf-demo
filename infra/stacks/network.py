from cdktf import TerraformStack, TerraformOutput
from constructs import Construct
from imports.vpc import Vpc
from imports.aws.provider import AwsProvider
from typing import List, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class VpcConfig:
    azs: List[str]
    cidr: str = "10.0.0.0/16"
    public_subnets: List[str] = field(default_factory=list)
    private_subnets: Optional[List[str]] = field(default=None)
    isolated_subnets: Optional[List[str]] = field(default=None)
    single_nat_gateway: bool = True
    private_subnets_tags: Optional[Dict[str, str]] = field(default=None)
    public_subnets_tags: Optional[Dict[str, str]] = field(default=None)
    isolated_subnets_tags: Optional[Dict[str, str]] = field(default=None)

class NetworkStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, config: VpcConfig):
        super().__init__(scope, id)
        AwsProvider(self, 'Aws', region='ap-southeast-1')
        self.vpc = Vpc(
            self,
            id,
            name=id,
            cidr=config.cidr,
            azs=config.azs,
            public_subnets=config.public_subnets,
            private_subnets=config.private_subnets,
            enable_nat_gateway=config.single_nat_gateway,
            public_subnet_tags={
                "kubernetes.io/role/elb": "1",
                "kubernetes.io/cluster/demo-eks": "owned"
            },
            private_subnet_tags={
                "kubernetes.io/role/internal-elb": "1",
                "kubernetes.io/cluster/demo-eks": "owned"
            }
        )

        TerraformOutput(self, "vpc-id", value=self.vpc.vpc_id_output)
        TerraformOutput(self, "public-subnets", value=self.vpc.public_subnets_output)
        TerraformOutput(self, "private-subnets", value=self.vpc.private_subnets_output)