from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, Token
from eks import EksStack, EksConfig
from network import NetworkStack, VpcConfig
from rds import RdsStack
class InfraStack(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        vpc = NetworkStack(
            self,
            "demo-vpc",
            config=VpcConfig(
                azs = ["ap-southeast-1a", "ap-southeast-1b"],
                cidr = "10.0.0.0/16",
                public_subnets = ["10.0.1.0/24", "10.0.2.0/24"],
                private_subnets = ["10.0.3.0/24", "10.0.4.0/24"],
                single_nat_gateway = True
            )
        )
        
        eks = EksStack(
            self,
            "demo-eks",
            config=EksConfig(
                cluster_name = "demo-eks",
                cluster_version = "1.32",
                cluster_endpoint_private_access = True,
                cluster_endpoint_public_access = True,
                cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"],
                vpc_id = vpc.vpc.vpc_id_output,
                subnet_ids=Token.as_list(vpc.vpc.private_subnets_output),
                control_plane_subnet_ids=Token.as_list(vpc.vpc.public_subnets_output) 
            )
        )
        eks.add_dependency(vpc)

        rds = RdsStack(
            self,
            "demo-rds",
            vpc_id=vpc.vpc.vpc_id_output,
            subnet_ids=Token.as_list(vpc.vpc.private_subnets_output)
        )
        rds.add_dependency(vpc)

app = App()
InfraStack(app, "cdktf-demo")
app.synth()