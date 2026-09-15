# 04. Client Onboarding Guide & Intake Questionnaire

When an engineering team wants to onboard a new application or microservice to the ZIPPO platform, they must complete the **Service Intake Questionnaire**. The answers are used to generate the application specification (`config.yaml`), Terraform deployment manifests, and CI/CD pipelines.

---

## 1. The Intake Questionnaire (What Clients Must Answer)

### Section A: Service Identity & Ownership
1. **Service Identifier:** What is the lowercase kebab-case name of the service? (e.g., `zippo-billing`, `zippo-notifications`).
2. **Repository Location:** GitHub organization and repo name (e.g., `epddp/ZIPPO-BILLING`).
3. **Owning Team & Tech Lead:** Who is responsible for maintaining this application?

### Section B: Container & Runtime Specifications
4. **Technology Stack:** Node.js, Python, Go, Java, static HTML/Nginx, etc.?
5. **Listening Port:** What TCP port does the application listen on? (e.g., `3000`, `8080`, `80`).
6. **Dockerfile Path:** Location of the Dockerfile in the repository (default: `./Dockerfile`).
7. **Resource Requirements:**
   * Fargate CPU units needed (`256`, `512`, `1024`, `2048`, `4096`).
   * Fargate Memory in MiB (`512`, `1024`, `2048`, `4096`, `8192`).
   * Initial desired replica count (default: `1`).

### Section C: Routing, Ingress & Health Checking
8. **Health Check Endpoint:** What HTTP GET route returns `200 OK`? (e.g., `/healthz` or `/api/v1/health`).
9. **Ingress Path Patterns:** What URL paths should route to this service from the shared Application Load Balancer? (e.g., `["/api/billing/*"]`).
10. **ALB Routing Priority:** What integer priority should this rule have? (Must be unique across all services on the ALB, e.g. `20`).
11. **Direct Port Requirement:** Does this service require its own dedicated external HTTPS port on the ALB? (e.g., port `3000` for admin or webhooks).

### Section D: Sidecars & Internal Dependencies
12. **Sidecar Containers:** Does the application require local in-task sidecars?
    * Sidecar container name (e.g. `redis`, `log-shipper`).
    * Image URI or ECR tag (e.g. `zippo-build:redis-alpine`).

### Section E: Configuration Variables (SSM Parameter Store)
13. **Environment Variables:** Provide a list of all non-sensitive configuration keys and their hierarchical paths in AWS SSM:
    * Example: `LOG_LEVEL` -> `/zippo-billing/log_level` (String)
    * Example: `PAYMENT_GATEWAY_URL` -> `/zippo-billing/gateway_url` (String)
14. **Encrypted Environment Variables:** Provide a list of parameters requiring KMS decryption:
    * Example: `WEBHOOK_SIGNING_KEY` -> `/zippo-billing/webhook_signing_key` (SecureString: true)

### Section F: Sensitive Credentials (AWS Secrets Manager)
15. **Secrets Manager References:** Provide the names of secrets stored in AWS Secrets Manager:
    * Example: `BILLING_DB_URI`
    * Example: `STRIPE_PRIVATE_KEY`

### Section G: AWS Service Permissions (IAM Task Role)
16. **Amazon SES:** Does the container need to send outbound transactional email? (`SES: true / false`).
17. **Amazon S3:** Does the container need read/write/delete access to an S3 bucket? (`S3_BUCKET: "<bucket-name>"`).
18. **Other AWS Services:** Does the service require access to SQS, DynamoDB, or SNS? (Requires platform team IAM extension).

---

## 2. Onboarding Workflow Checklist

```
  [ ] 1. Fill out Service Intake Questionnaire
  [ ] 2. Generate deploy/<env>/config.yaml using template
  [ ] 3. Validate config.yaml against schemas/app-config.schema.json
  [ ] 4. Run Terraform test suite (app_contract.tftest.hcl) locally or in CI
  [ ] 5. Platform Team provisions ECR repo & CodeBuild runner in ZIPPO-INFR
  [ ] 6. Application Team commits deploy/ directory and .github/workflows/ci.yml
  [ ] 7. Merge to main -> Automatic build, push, and Terraform apply
```
