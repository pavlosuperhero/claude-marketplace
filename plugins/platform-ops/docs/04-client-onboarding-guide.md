# 04. Client Onboarding Guide & Escalation Protocol

When an engineering team wants to onboard a new application or microservice to the platform, they must complete the **Service Intake Questionnaire**.

The platform provides a set of **predefined shared resources** (in `terraform.tfvars` and platform modules). If an application's requirements fit within these defaults, the onboarding is fully automated and self-service. If an application requires custom infrastructure outside these defaults, an **Escalation Request** to the Platform/Lifecycle team is triggered.

---

## 1. Predefined Platform Infrastructure Values

The following resources are managed centrally by the Platform/Lifecycle team in `lifecycle/<env>/terraform.tfvars` and `iac/aws-epam-ecs`:

| Resource | Predefined Platform Value | Source / Scope |
| :--- | :--- | :--- |
| **VPC** | Default AWS VPC | Platform Shared |
| **Subnet IDs** | `subnet-00ad56e8430188864`, `subnet-0e5f81a05db138a8f`, `subnet-0127b88eb7ccd10ed` | `terraform.tfvars:subnet_ids` |
| **ALB Security Group** | `sg-0b50f7bc21dea36a7` | `terraform.tfvars:alb_sg_id` |
| **Tasks Security Group** | `epam-east-eu` | `data.aws_security_group.tasks` |
| **Shared ALB** | `zippo-dev-alb` | `iac/aws-epam-ecs/vpc.tf` |
| **Shared Cluster** | `cheap-ecs` (Fargate + Fargate Spot) | `iac/aws-epam-ecs/ecs.tf` |
| **Shared Execution Role**| `cheap-ecs-exec` | `iac/aws-epam-ecs/rbac.tf` |
| **IAM Role Boundary** | `arn:aws:iam::<account_id>:policy/eo_role_boundary` | Enforced on all task roles |
| **Central Build ECR** | `<account_id>.dkr.ecr.<region>.amazonaws.com` | ECR repos: `zippo-build`, etc. |

---

## 2. The Intake Questionnaire & Escalation Matrix

### Section A: Identity & Ownership
1. **Service Identifier:** Kebab-case service name (e.g. `zippo-certs`).
2. **Repository Location:** GitHub organization and repo name (e.g. `epddp/ZIPPO-CERTS`).
3. **Owning Team & Tech Lead:** Service contact.

---

### Section B: Networking & Ingress (Escalation Check 1)
4. **Standard Question:** What container port does the app listen on? (e.g. `3000`, `8080`).
5. **Standard Question:** What ALB path pattern should route to this service? (e.g. `["/api/v1/certs/*"]`).
6. **Standard Question:** What rule priority should it have? (e.g. `5` for specific routes before `/api/*`).
7. **🚨 ESCALATION QUESTION:** *Does your service require a dedicated non-default VPC, private isolated subnets (no public IPs), or custom IP whitelist CIDRs on the ALB?*
   * **If YES -> ESCALATION TO PLATFORM TEAM:**
     * Platform team must provision dedicated subnets or update `alb_sg_id` (`sg-0b50f7bc21dea36a7`) in `lifecycle/<env>/terraform.tfvars`.
     * The app deployment cannot proceed until the platform team allocates these IDs.
8. **🚨 ESCALATION QUESTION:** *Does your service require a dedicated direct HTTPS port on the ALB (e.g., port 3000 or 8443) or a custom Route53 subdomain (e.g., `certs.zippo.dev`)?*
   * **If YES -> ESCALATION TO PLATFORM TEAM:**
     * Platform team must verify port availability and configure the listener certificate / Route 53 validation records in `ZIPPO-INFR/lifecycle/<env>`.

---

### Section C: Compute & Capacity (Escalation Check 2)
9. **Standard Sizing:** Choose standard Fargate CPU (`256`, `512`, `1024`, `2048`) and Memory (`512`, `1024`, `2048`, `4096`).
10. **🚨 ESCALATION QUESTION:** *Does your service require dedicated EC2 instances, GPU support, persistent EBS volumes, or compute > 4096 CPU units?*
    * **If YES -> ESCALATION TO PLATFORM TEAM:**
      * Shared cluster `cheap-ecs` only provides Fargate and Fargate Spot capacity.
      * Platform team must configure an EC2 or custom capacity provider.

---

### Section D: Cloud Permissions & IAM Boundaries (Escalation Check 3)
11. **Standard Self-Service Permissions:**
    * Amazon SES email sending (`SES: true`).
    * Amazon S3 bucket read/write (`S3_BUCKET: "zippo-files"`).
    * SSM parameter store reads (`/service/*`).
    * Secrets Manager secret reads (`JWT_SECRET`, `DB_URI`).
12. **🚨 ESCALATION QUESTION:** *Does your application need access to AWS services outside the standard set (e.g., DynamoDB, SQS, SNS, RDS, KMS, or cross-account roles)?*
    * **If YES -> ESCALATION TO PLATFORM TEAM:**
      * All task roles are gated by the organizational permission boundary `eo_role_boundary`.
      * Adding non-standard permissions requires the platform team to extend `iac/aws-epam-ecs-app/main.tf` or provide an approved inline IAM policy template.

---

## 3. The Onboarding Workflow (Standard vs. Escalated)

```
                    ┌──────────────────────────────────────────────┐
                    │ Client Completes Intake Questionnaire        │
                    └──────────────────────┬───────────────────────┘
                                           │
                           Escalation Questions Triggered?
                                           │
                          ┌────────────────┴────────────────┐
                          │                                 │
                       [ YES ]                           [ NO ]
                          │                                 │
                          ▼                                 ▼
           ┌─────────────────────────────┐   ┌─────────────────────────────┐
           │ ESCALATION TICKET TO        │   │ SELF-SERVICE PATH:          │
           │ PLATFORM TEAM:              │   │ • Use predefined VPC/SGs    │
           │ • Allocate new subnets/SGs  │   │ • Generate config.yaml      │
           │ • Add ECR repo & CodeBuild  │   │ • Validate with uv runner   │
           │ • Extend IAM boundary       │   │ • Run tftests -> Apply      │
           └──────────────┬──────────────┘   └─────────────────────────────┘
                          │ (Platform Applies)
                          ▼
           ┌─────────────────────────────┐
           │ App Team Resumes Onboarding │
           └─────────────────────────────┘
```
