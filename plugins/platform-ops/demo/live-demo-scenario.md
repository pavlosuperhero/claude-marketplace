# Live Demo Cheatsheet: The TDD IaC Self-Healing Loop

**Presentation Title:** *On the AI wave: LLM as an IaC Orchestrator (A TDD Approach)*  
**Demo Duration:** ~5-7 minutes  
**Target Scenario:** Onboarding the `zippo-certs` microservice to ECS Fargate.

---

## The Core Concept to Emphasize

> *"Don't try to craft a 50-line perfect prompt on the first try. Instead, give the AI a failing test and the execution tools to test, fail, and self-heal until green."*

---

## Step-by-Step Live Demo Flow

### Act 1: The Human Defines the Goal (The "Red" Phase) — 1 Minute
1. **Explain the challenge to the audience:**
   * *"We discovered the infrastructure specs for our new `zippo-certs` service. It needs port 3000, ALB path `/api/v1/certs/*`, S3 bucket access, and email permissions."*
2. **Show the test/contract:**
   * Open `schemas/app-config.schema.json` and `tests/tftests/app_contract.tftest.hcl`.
   * *"This contract defines our exact requirements: IAM boundary, health probes, ALB priority, and port routing."*

---

### Act 2: The Initial Failure (The Red Badge) — 1.5 Minutes
1. **Trigger an intentional failure scenario:**
   * In `deploy/dev/config.yaml`, set an invalid port or an unrouted ALB pattern (e.g., priority `10` which collides with `zippo-be`, or missing health check).
2. **Run the Orchestrator:**
   ```bash
   python3 scripts/tdd_orchestrator.py deploy/dev/config.yaml
   ```
3. **Point to the terminal:**
   * Large red badge appears: `🔴 [RED PHASE: SPECIFICATION VIOLATION / ASSERTION FAILED]`
   * Highlight to the audience: *"In traditional workflows, you'd find this out 20 minutes into deployment or in a staging incident. Here, our Python runner caught it in 1.4 seconds."*

---

### Act 3: Claude Enters the Loop (Self-Healing in Real Time) — 2.5 Minutes
1. **Prompt Claude Code:**
   > *"Run the platform-ops TDD orchestrator on `zippo-certs`. Analyze the failure, heal the configuration to satisfy all contract rules, and repeat until green."*
2. **Audience watches Claude's thought process:**
   * Claude inspects the diagnostic error emitted by the Python orchestrator.
   * Claude identifies the root cause (e.g., *"Rule priority 10 collides with backend; adjusting to priority 5 for higher precedence"*).
   * Claude edits `config.yaml` or the Terraform wrapper.
   * Claude triggers the orchestrator runner automatically.

---

### Act 4: The Green Phase (Mission Accomplished) — 1 Minute
1. **Terminal displays:**
   ```
   ══════════════════════════════════════════════════════════════════════
               AI-DRIVEN IAC ORCHESTRATOR: TDD LOOP
   ══════════════════════════════════════════════════════════════════════
   [*] Phase: Validating Specification (config.yaml)...
     ✓ Schema Contract: Valid (100% compliant with JSON Schema)
   [*] Phase: Executing Native Terraform Contract Tests (*.tftest.hcl)...

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED] (1.82s)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Summary: 23 Passed, 0 Failed, 0 Skipped.
   Ready for continuous deployment pipeline (ECR Release & TF Apply).
   ```
2. **Closing punchline for the audience:**
   * *"Zero lines of manual boilerplate written. Zero guesswork. The AI operated within strict guardrails, failed safely, fixed itself, and produced verified, compliant IaC."*
