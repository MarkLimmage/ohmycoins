# Developer C Consolidated Summary - Infrastructure & DevOps

**Role:** Infrastructure & DevOps Engineer  
**Track:** Phase 1 & 9 - Infrastructure Setup & Deployment  
**Status:** ✅ On Track - Weeks 1-6 Complete

---

## Executive Summary

As **Developer C**, my focus is on building and managing the cloud infrastructure and DevOps pipeline for the OhMyCoins project. Over the past six weeks, I have successfully established a robust, scalable, and cost-effective EKS environment on AWS, complete with a CI/CD pipeline for automated GitHub Actions runners.

The infrastructure is fully prepared to host the application components being developed by Developer A (Data) and Developer B (AI/ML), demonstrating the success of our parallel development strategy.

### Key Achievements (Weeks 1-6)

- ✅ **EKS Cluster Deployed**: Successfully provisioned the `OMC-test` EKS cluster in `ap-southeast-2` using `eksctl` and a new VPC.
- ✅ **Autoscaling GitHub Runners**: Implemented a two-node-group strategy with the Actions Runner Controller (ARC) and Cluster Autoscaler.
  - `system-nodes`: For critical services (e.g., ARC, Cluster Autoscaler).
  - `arc-runner-nodes`: For CI/CD jobs, scaling from 0 to 10 nodes on demand.
- ✅ **Cost Optimization**: The scale-to-zero configuration for runner nodes ensures we only pay for compute when CI/CD jobs are active, significantly reducing costs.
- ✅ **IAM & RBAC Hardening**: Resolved complex IAM permission issues for the Cluster Autoscaler by creating and attaching a custom policy. Configured all necessary Kubernetes RBAC roles.
- ✅ **Operational Tooling**: Developed a suite of bash scripts for common operational tasks (e.g., `run-db-migration.sh`, `run-tests.sh`).
- ✅ **Comprehensive Documentation**: Created and maintained detailed documentation for the EKS setup, autoscaling configuration, and operational runbooks.

---

## Detailed Sprint Summaries

### Weeks 5-6: EKS Autoscaling & CI/CD Integration

**Objective:** Implement a dynamic, cost-effective, and scalable solution for running GitHub Actions jobs on EKS.

**Deliverables:**
- **Cluster Autoscaler Deployment**: Deployed and configured the Kubernetes Cluster Autoscaler (v1.32.0) to manage the `arc-runner-nodes` node group.
- **IAM Policy for Autoscaler**: Diagnosed and fixed `AccessDenied` errors by creating a custom IAM policy (`OMC-ClusterAutoscalerPolicy`) with required permissions (`autoscaling:SetDesiredCapacity`, `ec2:Describe*`, etc.) and attaching it to the `system-nodes` instance role.
- **Taints and Tolerations**:
  - Tainted `system-nodes` with `CriticalAddonsOnly=true:NoSchedule` to reserve them for essential services.
  - Tainted `arc-runner-nodes` with `github-runners=true:NoSchedule` to dedicate them to CI/CD workloads.
  - Patched ARC and updated runner deployments to tolerate the respective taints.
- **GitHub Workflow Updates**: Modified `.github/workflows/*.yml` files to use `runs-on: [self-hosted, eks, test]`, directing jobs to the new EKS runners.
- **End-to-End Validation**: Successfully triggered a GitHub Actions workflow and observed the `arc-runner-nodes` group scale up from 0 to 1, run the job, and scale back down to 0.
- **Documentation**: Created `EKS_AUTOSCALING_CONFIGURATION.md` detailing the entire setup, including the IAM policy fix and design decisions.

**Outcome:** A fully automated, scalable, and cost-efficient CI/CD runner infrastructure is now operational, ready to support the project's development lifecycle.

---

### Weeks 3-4: Operational Scripts & Runbooks

**Objective:** Create tooling and documentation to streamline development, testing, and operational procedures.

**Deliverables:**
- **Operational Scripts**:
  - `run-db-migration.sh`: Automates running Alembic database migrations.
  - `run-tests.sh`: Executes the project's test suite in the correct environment.
  - `connect-to-db.sh`: Provides a quick way to connect to the PostgreSQL database for debugging.
  - `view-logs.sh`: Simplifies viewing logs for different application components.
- **Runbooks**:
  - `RUNBOOK_DATABASE_MANAGEMENT.md`: Detailed procedures for database backups, restores, and migrations.
  - `RUNBOOK_MONITORING_ALERTS.md`: Instructions for setting up and responding to monitoring alerts (placeholder for Prometheus/Grafana).
- **Initial Terraform Structure**: Set up the basic directory structure and state backend configuration for Terraform, in preparation for managing non-EKS AWS resources.

**Outcome:** A suite of scripts and runbooks that improve developer productivity, reduce manual errors, and establish standardized operational procedures.

---

### Weeks 1-2: Foundational EKS Cluster Setup

**Objective:** Provision the core Kubernetes cluster and networking infrastructure on AWS.

**Deliverables (Inferred from guide):**
- **VPC & Networking**: Defined and created a new, production-ready VPC with public and private subnets using `eksctl`.
- **EKS Cluster Provisioning**: Wrote the `eks-cluster-new-vpc.yml` configuration file.
- **Initial Node Group**: Deployed the `system-nodes` node group (`t3.medium`) to serve as the foundation for the cluster.
- **`kubectl` Configuration**: Configured `kubectl` to connect to the new `OMC-test` cluster.
- **ARC Installation**: Deployed the Actions Runner Controller (ARC) into the `actions-runner-system` namespace.

**Outcome:** A stable and secure EKS cluster was established, providing the foundation for all subsequent infrastructure and application deployments.

---

## Current Status & Next Steps

The core infrastructure is stable, scalable, and fully documented.

**Integration Readiness:**
- The EKS cluster is ready to host the FastAPI backend (Developer A) and the LangGraph agentic system (Developer B).
- The CI/CD pipeline is operational and can be used to build, test, and deploy container images for all application components.

**Next Steps (Weeks 7-12):**
1.  **Terraform Expansion (Weeks 7-8)**: Use Terraform to manage AWS resources like RDS, ElastiCache, and S3 buckets.
2.  **Monitoring & Logging (Weeks 9-10)**: Deploy Prometheus, Grafana, and Loki/Promtail to establish a comprehensive monitoring and logging stack.
3.  **CI/CD Pipeline for Deployments (Weeks 11-12)**: Create GitHub Actions workflows to automatically build and deploy the application to the EKS cluster.

The parallel development approach has been validated, as the infrastructure is ready and waiting for the application code without any blocking dependencies.

---

## Addendum: Terraform Staging Environment Deployment Fixes

**Date**: 2025-11-18
**Author**: GitHub Copilot

### 1. Overview

This section summarizes the series of changes made to the Terraform configuration to successfully deploy the `staging` environment. The deployment was failing due to several issues related to networking, IAM, RDS, and the Application Load Balancer.

### 2. Summary of Changes

The following files were modified to resolve the deployment errors:

#### a. `infrastructure/terraform/environments/staging/terraform.tfvars`

*   **Change**: Added explicit CIDR range variables for the VPC and its subnets (`vpc_cidr`, `public_subnet_cidrs`, `private_app_subnet_cidrs`, `private_db_subnet_cidrs`).
*   **Reason**: The original `cidrsubnet` function was creating overlapping CIDR ranges, causing `terraform apply` to fail. Defining explicit, non-overlapping ranges for each subnet tier resolved the conflict.

#### b. `infrastructure/terraform/modules/vpc/main.tf`

*   **Change**: The `aws_subnet` resources were updated to iterate over the new list variables (`var.public_subnet_cidrs`, etc.) instead of calculating CIDR blocks with `cidrsubnet`.
*   **Reason**: This change was necessary to consume the explicit CIDR ranges defined in the `.tfvars` file, giving us full control over the network layout.

#### c. `infrastructure/terraform/modules/iam/main.tf`

*   **Change**: The `aws_iam_openid_connect_provider` resource was replaced with a `data` source. The `aws_iam_role` for GitHub Actions was updated to reference the ARN from this data source.
*   **Reason**: An IAM OIDC provider for GitHub Actions already existed in the AWS account. Terraform was failing because it was trying to create a duplicate. Switching to a `data` source allows Terraform to look up and use the existing provider instead of creating a new one.

#### d. `infrastructure/terraform/modules/iam/outputs.tf`

*   **Change**: The `github_oidc_provider_arn` output was updated to source its value from the new `data.aws_iam_openid_connect_provider`.
*   **Reason**: To ensure the output reflects the ARN of the actual provider being used.

#### e. `infrastructure/terraform/modules/rds/main.tf`

*   **Change**: The `apply_method = "pending-reboot"` argument was moved from the `aws_db_instance` resource to the `parameter` blocks within the `aws_db_parameter_group` resource.
*   **Reason**: The `apply_method` for database parameters must be specified on the parameters themselves within the parameter group, not on the database instance. This correction fixed the RDS modification error.

#### f. `infrastructure/terraform/modules/alb/main.tf`

*   **Change**: The default action for the HTTP listener (`aws_lb_listener`) was changed from a `redirect` action to a `forward` action pointing to the frontend service's target group.
*   **Reason**: The final deployment error indicated that the ECS service's target group was not associated with any listener. The HTTP listener was incorrectly configured to redirect all traffic to HTTPS instead of forwarding it to a target. This change ensures that incoming HTTP traffic is correctly routed to the frontend service.

### 3. New Files Created

*   **`CLEANUP.md`**: This file was created to provide clear instructions on how to tear down the infrastructure using `terraform destroy` for each environment, ensuring a clean and repeatable process.

### 4. Conclusion

These changes resolved all blocking issues and resulted in a successful `terraform apply` for the `staging` environment. The infrastructure is now deployed and operational.

```
