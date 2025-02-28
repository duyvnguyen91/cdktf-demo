from constructs import Construct
from cdktf import TerraformStack
from imports.kubernetes.provider import KubernetesProvider
from imports.kubernetes.deployment_v1 import DeploymentV1, DeploymentV1Metadata, DeploymentV1Spec, DeploymentV1SpecTemplate, DeploymentV1SpecTemplateMetadata, DeploymentV1SpecTemplateSpec, DeploymentV1SpecTemplateSpecContainer, DeploymentV1SpecTemplateSpecContainerPort

class K8sStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # Configure the Kubernetes provider
        KubernetesProvider(self, "K8sProvider", config_path="~/.kube/config")

        # Define metadata
        metadata = DeploymentV1Metadata(name="nginx-deployment")

        # Define container
        container = DeploymentV1SpecTemplateSpecContainer(
            name="nginx",
            image="nginx:latest",
            port=[DeploymentV1SpecTemplateSpecContainerPort(
              container_port=80
            )]
        )

        # Define Pod spec
        template_spec = DeploymentV1SpecTemplateSpec(container=[container])

        # Define Pod template metadata
        template_metadata = DeploymentV1SpecTemplateMetadata(labels={"app": "nginx"})

        # Define Pod template
        template = DeploymentV1SpecTemplate(
            metadata=template_metadata,
            spec=template_spec
        )

        # Define Deployment spec
        spec = DeploymentV1Spec(
            replicas="1",
            selector={"match_labels": {"app": "nginx"}},
            template=template
        )

        # Create Deployment
        DeploymentV1(
            self,
            "nginx-deployment",
            metadata=metadata,
            spec=spec
        )