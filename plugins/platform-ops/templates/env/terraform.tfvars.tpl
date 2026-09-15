ecr_repo   = ["zippo-build", "zippo-fe", "zippo-be"]
project    = "{{PROJECT_NAME}}"
subnet_ids = [{{SUBNET_IDS}}]
alb_sg_id  = "{{ALB_SG_ID}}"

codebuild_github_pat_secret_name     = "{{GITHUB_PAT_SECRET_NAME}}"
codebuild_module_ssh_key_secret_name = "{{MODULE_SSH_KEY_SECRET_NAME}}"

codebuild_projects = {
  "ZIPPO-INFRA-{{ENVIRONMENT}}" = {
    source_location     = "https://github.com/epddp/ZIPPO-INFR"
    runner_tag_ssm_path = "/ci/runners/terraform/tag"
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
