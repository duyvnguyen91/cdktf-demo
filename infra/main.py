from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, Token
from imports.aws.provider import AwsProvider
# from eks import Eks
from network import NetworkStack

class InfraStack(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        AwsProvider(self, 'Aws', region='ap-southest-1')
        
        vpc = NetworkStack(
            self,
            "demo-vpc",
            config={
                "azs": ["ap-southeast-1a", "ap-southeast-1b"],
                "cidr": "10.0.0.0/16",
                "publicSubnets": ["10.0.1.0/24", "10.0.2.0/24"],
                "privateSubnets": ["10.0.3.0/24", "10.0.4.0/24"],
                "singleNatGateway": True
            }
        )
        
        

app = App()
InfraStack(app, "cdktf-demo")
app.synth()