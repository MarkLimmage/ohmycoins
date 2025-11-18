# Infrastructure Cleanup

This document provides the steps to tear down all the AWS infrastructure created for the Oh My Coins project.

## ⚠️ Warning

The following commands are destructive and will permanently delete all the resources managed by Terraform in the staging environment. This includes the VPC, ECS cluster, services, RDS database, and ElastiCache Redis cluster.

**Proceed with caution. This action cannot be undone.**

## Teardown Steps

1.  **Navigate to the Terraform environment directory:**

    Open your terminal and change to the directory containing the Terraform configuration for the staging environment.

    ```bash
    cd /home/mark/omc/ohmycoins/infrastructure/terraform/environments/staging
    ```

2.  **Initialize Terraform:**

    If you haven't already, initialize Terraform in this directory.

    ```bash
    terraform init
    ```

3.  **Destroy the infrastructure:**

    Run the `terraform destroy` command. You will be prompted to confirm the destruction of the resources. Type `yes` to proceed.

    ```bash
    terraform destroy
    ```

    Alternatively, you can skip the confirmation prompt by using the `-auto-approve` flag.

    ```bash
    terraform destroy -auto-approve
    ```

Terraform will now proceed to delete all the resources. This process may take several minutes. Once completed, all the infrastructure will be removed.
