# 01. Architecture Overview

## 1. Executive Summary

ZIPPO is a containerized microservices platform running on Amazon Web Services (AWS) in the `eu-central-1` (Frankfurt) region. The system separates the operational topology into two decoupled layers:

1. **The Lifecycle / Platform Foundation (`ZIPPO-INFR`):** Shared, persistent infrastructure providing networking, load balancing, DNS, TLS termination, container orchestration clusters, shared execution IAM roles, and self-hosted CI/CD runners.
2. **The Microservice Application Layer (`ZIPPO-BE`, `ZIPPO-FE`, etc.):** Decoupled repositories hosting application logic, Docker containers, declarative deployment manifests (`config.yaml`), and dedicated ECS services.

```
                             INTERNET TRAFFIC
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │   Route 53 / Custom Domain   │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │         Shared Application Load Balancer (ALB)         │
       │           Port 80 (HTTP 301 -> HTTPS 443)              │
       │           Port 443 (TLS ACM / Default 404)             │
       └───────┬────────────────────────────┬───────────────────┘
               │                            │
      Priority: 10 (/api/*)        Priority: 100 (/*)
               │                            │
               ▼                            ▼
       ┌───────────────┐            ┌───────────────┐
       │   zippo-be    │            │   zippo-fe    │
       │ Target Group  │            │ Target Group  │
       └───────┬───────┘            └───────┬───────┘
               │ (port: 3000)               │ (port: 80)
               ▼                            ▼
   ┌───────────────────────┐    ┌───────────────────────┐
   │  ECS Fargate Task     │    │  ECS Fargate Task     │
   │  ┌─────────────────┐  │    │  ┌─────────────────┐  │
   │  │ Node.js NestJS  │  │    │  │ React / Nginx   │  │
   │  └─────────────────┘  │    │  └─────────────────┘  │
   │  ┌─────────────────┐  │    └───────────────────────┘
   │  │ Redis Sidecar   │  │
   │  └─────────────────┘  │
   └───────────┬───────────┘
               │
               ▼
     ┌───────────────────┐
     │ MongoDB EC2 / AMI │
     │  (Standalone DB)  │
     └───────────────────┘
```

---

## 2. Component Directory

| Component | Responsibility | Repository / Module |
| :--- | :--- | :--- |
| **Shared Network & ALB** | Default VPC, public subnets, ingress ALB, ACM TLS cert, port 443 listener rules | `ZIPPO-INFR/iac/aws-epam-ecs` |
| **ECS Cluster** | `cheap-ecs` cluster with `FARGATE` and `FARGATE_SPOT` capacity providers | `ZIPPO-INFR/iac/aws-epam-ecs/ecs.tf` |
| **Application Module** | Standardized, reusable Terraform module generating task definitions, roles, services, and target groups | `ZIPPO-INFR/iac/aws-epam-ecs-app` |
| **CI/CD Runners** | Ephemeral GitHub Actions runners on AWS CodeBuild with dedicated VPC access and ECR pull cache | `ZIPPO-INFR/iac/aws-epam-ecs/codebuild.tf` |
| **Configuration Store** | AWS Systems Manager (SSM) Parameter Store & AWS Secrets Manager | AWS native via IAM scoped roles |
| **Backend App** | NestJS REST API with Redis cache sidecar and MongoDB connectivity | `ZIPPO-BE/deploy/dev` |
| **Frontend App** | React SPA served via Nginx with client-side routing | `ZIPPO-FE/deploy/dev` |

---

## 3. Communication & Ingress Patterns

1. **Ingress Routing:**
   * All external HTTP requests arrive at port 80 of the shared ALB and receive an immediate `301 Moved Permanently` to port 443 HTTPS.
   * Path patterns evaluate against listener rules in order of priority:
     * `/api/*` (Priority 10) forwards to `zippo-be` target group.
     * `/*` (Priority 100) forwards to `zippo-fe` target group.
     * Unmatched requests return an immediate `404 Not Found`.
2. **Direct Ports:**
   * For direct backend debugging or dedicated socket listeners, an optional direct HTTPS port (e.g. port 3000) can be attached to the ALB forwarding directly to the backend target group.
3. **Internal App-to-App & Sidecars:**
   * In-process sidecars (e.g., Redis container in `zippo-be`) communicate via `localhost:<port>` within the Fargate task network namespace.
