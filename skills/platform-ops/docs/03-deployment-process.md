# 03. Deployment Process

This document details exactly how services and infrastructure changes are deployed across the ZIPPO platform.

---

## 1. End-to-End Application Deployment Flow

Every application repository (`ZIPPO-BE`, `ZIPPO-FE`, or any new service) executes an autonomous, 5-stage deployment pipeline triggered upon push or pull request to the `main` branch.

```
┌─────────────┐     ┌────────────────┐     ┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. Lint &   │────▶│ 2. Docker ECR  │────▶│ 3. SSM Release │────▶│ 4. Terraform │────▶│ 5. ECS Task  │
│    Test     │     │    Push        │     │    Tag Update  │     │    Apply     │     │    Rolling   │
└─────────────┘     └────────────────┘     └────────────────┘     └──────────────┘     └──────────────┘
```

### Stage 1: Continuous Integration (Lint & Test)
* **Runner:** Ephemeral AWS CodeBuild container (`codebuild-ZIPPO-<APP>-<run_id>`).
* **Actions:**
  * Dependency installation with cache restoration (`~/.npm`).
  * Static code analysis & linting (`npm run lint`).
  * Automated unit & integration tests (`npm run test:ci`).
  * Code coverage report generation.

### Stage 2: Container Image Build & Registry Push
* **Actions:**
  * Resolve AWS Account ID dynamically via `aws sts get-caller-identity`.
  * Compute release tag: `IMAGE_TAG="${SHORT_SHA}-${DATE_TAG}"` (e.g. `41d0162-15-09-26-12-00`).
  * Authenticate Docker daemon against Amazon ECR:
    ```bash
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    ```
  * Build container using root `Dockerfile`.
  * Push image to ECR repository (`${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/<service-name>:${IMAGE_TAG}`).

### Stage 3: Release Version Registry Update
* **SSM Parameter Store Key:** `/ci/<service-name>/image_tag`
* **Command:**
  ```bash
  aws ssm put-parameter --name "/ci/${SERVICE_NAME}/image_tag" --value "${IMAGE_TAG}" --overwrite
  ```
* **Rationale:** Decouples image production from infrastructure updates. Terraform reads this parameter via `data "aws_ssm_parameter" "image_tag"` to determine which container image to assign to the ECS task definition.

### Stage 4: Terraform Plan & Apply
* **Path:** `deploy/<env>/`
* **Module Resolution:** Configures Git credentials to fetch the private module `ZIPPO-INFR//iac/aws-epam-ecs-app` using either the GitHub PAT or Deploy SSH key.
* **Commands:**
  ```bash
  terraform init -upgrade
  terraform fmt -check
  terraform validate
  terraform plan
  terraform apply -auto-approve
  ```

### Stage 5: ECS Fargate Rolling Deployment
* ECS registers a new revision of the task definition with the new image tag.
* Fargate starts new tasks, runs health checks against the target group, verifies healthy status, drains existing tasks, and completes zero-downtime rolling update.

---

## 2. Infrastructure & Lifecycle Deployment Flow

Platform infrastructure changes in `ZIPPO-INFR` follow a controlled lifecycle:

1. **State Isolation:**
   * Infrastructure state is isolated in S3 (`zippo-terraform-state-bucket`, key `zippo` or `zippo-<env>`).
2. **Execution Steps:**
   ```bash
   cd lifecycle/<env>
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```
3. **Database Changes:**
   * MongoDB AMI changes: Built via HashiCorp Packer (`mongodb-ami.pkr.hcl`) and deployed via `iac/mongodb/ec2.tf`.

---

## 3. Dynamic Configuration & Secrets Provisioning Flow

When an application requires a new environment variable or secret, it is provisioned through the automated workflow in `ZIPPO-INFR/.github/workflows/provision-config.yml`:

1. Developer triggers `workflow_dispatch` with:
   * Service (`zippo-be`, `zippo-fe`, etc.)
   * Type (`variable` or `secret`)
   * Name (`REDIS_PORT` or `STRIPE_API_KEY`)
   * SSM Path (`/zippo-be/redis_port`)
   * Secure flag (`true` or `false`)
2. Workflow creates the parameter or secret in AWS with value `"PLACEHOLDER"`.
3. Workflow updates `deploy/<service>/<env>/config.yaml`.
4. Workflow automatically opens a Git branch and Pull Request for review.
5. Admin updates the actual sensitive value in AWS Systems Manager or Secrets Manager before the PR is merged.
