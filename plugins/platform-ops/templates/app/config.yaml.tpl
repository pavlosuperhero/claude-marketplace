# Application Deployment Specification
# Conforms to: schemas/app-config.schema.json
NAME: {{APP_NAME}}
PORT: {{APP_PORT}}
HEALTH: "{{HEALTH_PATH}}"
CPU: {{CPU_UNITS}}         # 256 | 512 | 1024 | 2048 | 4096
MEMORY: {{MEMORY_MIB}}    # 512 | 1024 | 2048 | 3072 | 4096 | 5120 | 6144 | 7168 | 8192
DESIRED_COUNT: {{DESIRED_COUNT}} # 0-20, default 1
SES: {{ENABLE_SES}} # true | false
S3_BUCKET: "{{S3_BUCKET_NAME}}" # S3 bucket name for PutObject/GetObject/DeleteObject access

# Sidecars (optional, e.g. redis cache)
# SIDECARS:
#   - name: redis
#     ecr_image: "zippo-build:redis-alpine"

ALB:
  health_check: "{{HEALTH_PATH}}"
  path_patterns: [{{PATH_PATTERNS}}] # e.g. ["/api/{{APP_NAME}}/*"]
  priority: {{ALB_PRIORITY}} # Integer (e.g. 50, unique across services)
  # direct_port: {{DIRECT_PORT}} # Optional dedicated port on the ALB

ENV_VARS:
  - name: AWS_REGION
    ssm_path: "/{{SERVICE_ID}}/aws_region"
    secure: false
  # Add other plain or SecureString environment variables below:
  # - name: DB_NAME
  #   ssm_path: "/{{SERVICE_ID}}/database_name"
  #   secure: false

SECRETS:
  # Add AWS Secrets Manager secret identifiers:
  # - name: DB_URI
  # - name: JWT_SECRET

