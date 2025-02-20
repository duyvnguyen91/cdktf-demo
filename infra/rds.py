from imports.aws import RdsInstance

class DBStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, vpc):
        super().__init__(scope, id)

        self.db = RdsInstance(self, "Database", engine="postgres", instance_class="db.t3.micro", vpc_security_group_ids=[vpc.vpc.id])
