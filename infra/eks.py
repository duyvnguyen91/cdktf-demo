from cdktf import TerraformStack, TerraformOutput
from constructs import Construct
from imports.eks import Eks
from imports.helm.provider import HelmProvider
from imports.kubernetes.provider import KubernetesProvider
from imports.kubectl.provider import KubectlProvider
from imports.aws.data_aws_eks_cluster_auth import DataAwsEksClusterAuth
from imports.aws.provider import AwsProvider
from imports.eksClusterAutoscaler import EksClusterAutoscaler
from imports.eksLoadBalancerController import EksLoadBalancerController
from imports.helm.release import Release
from imports.irsaEks import IrsaEks
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class EksConfig:
    cluster_name: str
    cluster_version: str
    cluster_endpoint_private_access: bool
    cluster_endpoint_public_access: bool
    vpc_id: str
    subnet_ids: List[str]
    control_plane_subnet_ids: List[str]
    cluster_endpoint_public_access_cidrs: Optional[List[str]] = field(default=None)

class EksStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, config: EksConfig):
        super().__init__(scope, id)
        AwsProvider(self, 'Aws', region='ap-southeast-1')
        self.eks = Eks(
          self,
          id,
          cluster_name=config.cluster_name,
          cluster_version=config.cluster_version,
          cluster_endpoint_private_access=config.cluster_endpoint_private_access,
          cluster_endpoint_public_access=config.cluster_endpoint_public_access,
          cluster_endpoint_public_access_cidrs=config.cluster_endpoint_public_access_cidrs,
          cluster_addons={
            "coredns": {
              "most_recent": "true"
            },
            "kube-proxy": {
              "most_recent": "true"
            },
            "vpc-cni": {
              "most_recent": "true"
            },
            "aws-ebs-csi-driver": {
              "service_account_role_arn": f"arn:aws:iam::241533152550:role/{config.cluster_name}-ebs-csi-role",
              "most_recent": "true"
            },
          },
          vpc_id=config.vpc_id,
          subnet_ids=config.subnet_ids,
          create_kms_key=True,
          cluster_security_group_additional_rules={
            "egress_nodes_ephemeral_ports_tcp": {
              "description": "To node 1025-65535",
              "protocol": "tcp",
              "from_port": "1025",
              "to_port": "65535",
              "type": "egress",
              "source_node_security_group": "true"
            }
          },
          node_security_group_additional_rules={
            "ingress_self_all": {
              "description": "Node to node all ports/protocols",
              "protocol": "-1",
              "from_port": "0",
              "to_port": "0",
              "type": "ingress",
              "self": "true"
            },
            "egress_all": {
              "description": "Node all egress",
              "protocol": "-1",
              "from_port": "0",
              "to_port": "0",
              "type": "egress",
              "cidr_blocks": ["0.0.0.0/0"],
              "ipv6_cidr_blocks": ["::/0"]
            }
          },
          eks_managed_node_groups={
            "default": {
              "create_launch_template": "true",
              "launch_template_name": "default-pool",
              "launch_template_use_name_prefix": "true",
              "min_size": "2",
              "max_size": "5",
              "desired_size": "2",
              "instance_types": ["t3.large"],
              "disk_size": 30,
              "capacity_type": "SPOT",
              "iam_role_attach_cni_policy": "true",
              "iam_role_additional_policies": {
                "AmazonEKSWorkerNodePolicy": "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                "additional": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
              },
              "instance_refresh": {
                "strategy": "Rolling",
                "preferences": {
                  "min_healthy_percentage": "66"
                }
              },
              "labels": {
                "spot": "true"
              },
              "update_config": {
                "max_unavailable_percentage": "50",
              },
              "post_bootstrap_user_data": """<<-EOT
                cd /tmp
                sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
                sudo systemctl enable amazon-ssm-agent
                sudo systemctl start amazon-ssm-agent
                EOT""",
              "metadata_options": {
                  "http_endpoint": "enabled",
                  "http_tokens": "optional",
                  "http_put_response_hop_limit": 2,
                  "instance_metadata_tags": "enabled"
              },
              "tag": {
                  "Team": "devops",
                  "Environment": "test",
                  "Terraform": "true"
              }
            }
          },
          authentication_mode="API_AND_CONFIG_MAP",
          enable_cluster_creator_admin_permissions=True,
          tags={
            "Team": "devops",
            "Environment": "demo",
            "Terraform": "true"
          }
        )        
        
        # Helm Provider
        helm_provider = HelmProvider(
          scope=self, 
          id=f"{id}-helm-provider",
          kubernetes={
            "host": self.eks.cluster_endpoint_output,
            "cluster_ca_certificate": f"${{base64decode({self.eks.cluster_certificate_authority_data_output})}}",
            "exec": {
                "api_version": "client.authentication.k8s.io/v1beta1",
                "args": ["eks", "get-token", "--cluster-name", config.cluster_name],
                "command": "aws"
            }
          }
        )
        
        # Kubernetes Provider
        k8s_provider = KubernetesProvider(
          scope=self,
          id=f"{id}-k8s-provider",
          host=self.eks.cluster_endpoint_output,
          cluster_ca_certificate=f"${{base64decode({self.eks.cluster_certificate_authority_data_output})}}",
          exec=[{
              "apiVersion": "client.authentication.k8s.io/v1beta1",
              "args": ["eks", "get-token", "--cluster-name", config.cluster_name],
              "command": "aws"
          }]
        )

        # AWS EKS Cluster Authentication Data
        data_eks_cluster_auth = DataAwsEksClusterAuth(
            scope=self,
            id_=f"{id}-cluster-auth",
            name=self.eks.cluster_name_output
        )

        # Kubectl Provider
        kubectl_provider = KubectlProvider(
            scope=self, 
            id=f"{id}-kubectl-provider",
            host=self.eks.cluster_endpoint_output,
            cluster_ca_certificate=f"${{base64decode({self.eks.cluster_certificate_authority_data_output})}}",
            token=data_eks_cluster_auth.token,
            load_config_file=False
        )

        # EKS Cluster Autoscaler
        eks_cluster_autoscaler = EksClusterAutoscaler(
            scope=self,
            id=f"{id}-cluster-autoscaler",
            cluster_name=config.cluster_name,
            cluster_identity_oidc_issuer=self.eks.oidc_provider_output,
            cluster_identity_oidc_issuer_arn=self.eks.oidc_provider_arn_output,
        )

        # EKS Load Balancer Controller
        eks_load_balancer_controller = EksLoadBalancerController(
            scope=self,
            id=f"{id}-loadbalancer-controller",
            cluster_name=config.cluster_name,
            cluster_identity_oidc_issuer=self.eks.oidc_provider_output,
            cluster_identity_oidc_issuer_arn=self.eks.oidc_provider_arn_output,
        )

        # Helm Release for Metrics Server
        metrics_server_release = Release(
            scope=self,
            id_=f"{id}-metrics-server",
            name="metrics-server",
            repository="https://kubernetes-sigs.github.io/metrics-server/",
            chart="metrics-server",
            namespace="kube-system",
        )

        ebs_csi_irsa = IrsaEks(
          scope=self,
          id=f"{id}-ebs-csi-irsa",
          role_name=f"{id}-ebs-csi-role",
          attach_ebs_csi_policy=True,
          oidc_providers={
            "main": {
              "provider_arn": self.eks.oidc_provider_arn_output,
              "namespace_service_accounts": ["kube-system:ebs-csi-controller-sa"]
            }
          }
        )

        # Terraform Output for OIDC Provider
        TerraformOutput(
            scope=self,
            id="oidc-provider",
            value=self.eks.oidc_provider_output
        )

        # Terraform Output for OIDC Provider ARN
        TerraformOutput(
            scope=self,
            id="oidc-provider-arn",
            value=self.eks.oidc_provider_arn_output
        )
