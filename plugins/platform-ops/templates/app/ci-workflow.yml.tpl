name: {{SERVICE_DISPLAY_NAME}} CI/CD

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch: {}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  AWS_REGION: eu-central-1
  SERVICE_NAME: {{SERVICE_ID}}

permissions:
  contents: read

jobs:
  lint-and-test:
    if: ${{ !contains(github.event.head_commit.message || '', '[skip-ci]') }}
    runs-on:
      - codebuild-{{RUNNER_PROJECT_NAME}}-${{ github.run_id }}-${{ github.run_attempt }}
      - buildspec-override:true
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: Run Linters and Unit Tests
        run: |
          echo "Running application automated tests..."
          {{TEST_COMMAND}}

  build:
    if: ${{ !contains(github.event.head_commit.message || '', '[skip-ci]') }}
    needs: lint-and-test
    runs-on:
      - codebuild-{{RUNNER_PROJECT_NAME}}-${{ github.run_id }}-${{ github.run_attempt }}
      - buildspec-override:true
    timeout-minutes: 20
    outputs:
      image_tag: ${{ steps.vars.outputs.image_tag }}
    steps:
      - uses: actions/checkout@v4
      - name: Set Image & ECR Variables
        id: vars
        run: |
          ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
          SHORT_SHA=$(git rev-parse --short HEAD)
          DATE_TAG=$(date +'%d-%m-%y-%H-%M')
          IMAGE_TAG="${SHORT_SHA}-${DATE_TAG}"
          ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}"
          echo "ACCOUNT_ID=$ACCOUNT_ID"   >> $GITHUB_ENV
          echo "IMAGE_TAG=$IMAGE_TAG"     >> $GITHUB_ENV
          echo "ECR_REPO=$ECR_REPO"       >> $GITHUB_ENV
          echo "image_tag=$IMAGE_TAG"     >> $GITHUB_OUTPUT

      - name: Build and Push Docker Container to ECR
        run: |
          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
          docker build -t "$ECR_REPO:$IMAGE_TAG" -f "$GITHUB_WORKSPACE/Dockerfile" "$GITHUB_WORKSPACE"
          docker push "$ECR_REPO:$IMAGE_TAG"

  update-image-tag:
    if: ${{ !contains(github.event.head_commit.message || '', '[skip-ci]') && github.ref == 'refs/heads/main' }}
    needs: build
    runs-on:
      - codebuild-{{RUNNER_PROJECT_NAME}}-${{ github.run_id }}-${{ github.run_attempt }}
      - buildspec-override:true
    timeout-minutes: 10
    steps:
      - name: Update Service Image Tag in AWS SSM
        run: |
          aws ssm put-parameter --name "/ci/${SERVICE_NAME}/image_tag" --value "${{ needs.build.outputs.image_tag }}" --overwrite

  terraform-plan:
    name: Terraform Plan
    if: ${{ !failure() && !cancelled() && !contains(github.event.head_commit.message || '', '[skip-ci]') && github.ref == 'refs/heads/main' }}
    needs: [build, update-image-tag]
    runs-on:
      - codebuild-{{RUNNER_PROJECT_NAME}}-${{ github.run_id }}-${{ github.run_attempt }}
      - buildspec-override:true
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials for Terraform Modules
        run: git config --global url."https://x-access-token:${GITHUB_MODULE_PAT}@github.com".insteadOf "https://github.com"
      - name: Terraform Init
        run: terraform -chdir=deploy/dev init -upgrade
      - name: Terraform Format Check
        run: terraform -chdir=deploy/dev fmt -check
      - name: Terraform Validate
        run: terraform -chdir=deploy/dev validate
      - name: Terraform Plan
        run: terraform -chdir=deploy/dev plan
      - name: Cleanup Git Credentials
        if: always()
        run: git config --global --unset-all url."https://x-access-token:${GITHUB_MODULE_PAT}@github.com".insteadOf || true

  terraform-apply:
    name: Terraform Apply
    if: ${{ !failure() && !cancelled() && !contains(github.event.head_commit.message || '', '[skip-ci]') && github.ref == 'refs/heads/main' }}
    needs: terraform-plan
    environment: dev
    runs-on:
      - codebuild-{{RUNNER_PROJECT_NAME}}-${{ github.run_id }}-${{ github.run_attempt }}
      - buildspec-override:true
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials for Terraform Modules
        run: git config --global url."https://x-access-token:${GITHUB_MODULE_PAT}@github.com".insteadOf "https://github.com"
      - name: Terraform Init
        run: terraform -chdir=deploy/dev init -upgrade
      - name: Terraform Apply
        run: terraform -chdir=deploy/dev apply -auto-approve
      - name: Cleanup Git Credentials
        if: always()
        run: git config --global --unset-all url."https://x-access-token:${GITHUB_MODULE_PAT}@github.com".insteadOf || true
