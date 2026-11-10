ecr_repo   = [{{ECR_REPOSITORIES}}]
project    = "{{PROJECT_NAME}}"
region     = "{{AWS_REGION}}"
subnet_ids = [{{SUBNET_IDS}}]
alb_sg_id  = "{{ALB_SG_ID}}"

codebuild_github_pat_secret_name     = "{{GITHUB_PAT_SECRET_NAME}}"
codebuild_module_ssh_key_secret_name = "{{MODULE_SSH_KEY_SECRET_NAME}}"

codebuild_projects = {
  "{{RUNNER_PROJECT_NAME}}" = {
    source_location     = "{{INFRA_REPOSITORY_URL}}"
    runner_tag_ssm_path = "{{RUNNER_TAG_SSM_PATH}}"
    buildspec           = <<-EOT
    version: 0.2
    phases:
      build:
        commands:
          - echo "GitHub Actions runner - Terraform ({{ENVIRONMENT}})"
    EOT
    webhook_filters = [
      [{ type = "EVENT", pattern = "WORKFLOW_JOB_QUEUED" }]
    ]
  }
}
