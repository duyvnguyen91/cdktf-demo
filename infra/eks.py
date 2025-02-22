from cdktf import TerraformStack, TerraformOutput
from constructs import Construct
from imports.eks import Eks
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    cluster_name: str
    cluster_version: str
    cluster_endpoint_private_access: bool
    cluster_endpoint_public_access: bool
    vpc_id: str
    subnet_ids: List[str]
    control_plane_subnet_ids: List[str]
    cluster_endpoint_public_access_cidrs: Optional[List[str]] = field(default=None)

class NetworkStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, config: Config):
        super().__init__(scope, id)
        
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
            }
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
              "use_custom_launch_template": "false",
              "min_size": "1",
              "max_size": "5",
              "desired_size": "1",
              "instance_types": ["t3.small"],
              "disk_size": 30,
              "capacity_type": "SPOT",
              "iam_role_attach_cni_policy": "true",
              "iam_role_additional_policies": {
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
              "tags": {
                  "Team": "devops",
                  "Environment": "test",
                  "Terraform": "true"
              }
            }
          },
          authentication_mode="API_AND_CONFIG_MAP",
          tags={
            "Team": "devops",
            "Environment": "demo",
            "Terraform": "true"
          }

          
          
        )