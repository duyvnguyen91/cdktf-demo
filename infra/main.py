from cdktf import App
from constructs import Construct
from imports.eks import Eks
from imports.vpc import Vpc
from k8s_deployment import K8sDeploymentStack

class InfraStack(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        AwsProvider(self, 'Aws', region='ap-southest-1')
        my_vpc = Vpc(self, 'MyVpc',
                     name='my-vpc',
                     cidr='10.0.0.0/16',
                     azs=['ap-southest-1a', 'ap-southest-1b', 'ap-southest-1c'],
                     private_subnets=['10.0.1.0/24',
                                      '10.0.2.0/24', '10.0.3.0/24'],
                     public_subnets=['10.0.101.0/24',
                                     '10.0.102.0/24', '10.0.103.0/24'],
                     enable_nat_gateway=True
                     )

        my_eks = Eks(self, 'MyEks',
                     cluster_name='my-eks',
                     subnets=Token().as_list(my_vpc.private_subnets_output),
                     vpc_id=Token().as_string(my_vpc.vpc_id_output),
                     manage_aws_auth=False,
                     cluster_version='1.21'
                     )

        TerraformOutput(self, 'cluster_endpoint',
                        value=my_eks.cluster_endpoint_output
                        )

        TerraformOutput(self, 'create_user_arn',
                        value=DataAwsCallerIdentity(self, 'current').arn
                        )


app = App()
InfraStack(app, "cdktf-demo")
app.synth()
