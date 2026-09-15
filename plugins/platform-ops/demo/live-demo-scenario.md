# Live Demo Cheatsheet: The TDD IaC Self-Healing Loop

**Presentation Title:** *On the AI wave: LLM as an IaC Orchestrator (A TDD Approach)*  
**Demo Duration:** ~7-8 minutes (drop Act 3b to fit 6 minutes — but it is the strongest act, so cut elsewhere first)  
**Target Scenario:** Onboarding the `zippo-certs` microservice to ECS Fargate.

---

## The Core Concept to Emphasize

> *"Don't try to craft a 50-line perfect prompt on the first try. Instead, give the AI a failing test and the execution tools to test, fail, and self-heal until green."*

> *"— and give it a hard boundary where it must stop and ask instead. An agent that will do anything to reach green will eventually reach green by breaking something. The exit-code contract (`0` verified / `1` fix it / `2` ask a human) is what makes the loop safe to run unattended."*

---

## Step-by-Step Live Demo Flow

### Act 1: The Human Defines the Goal (The "Red" Phase) — 1 Minute
1. **Explain the challenge to the audience:**
   * *"We discovered the infrastructure specs for our new `zippo-certs` service. It needs port 3000, ALB path `/api/v1/certs/*`, S3 bucket access, and email permissions."*
2. **Show the test/contract:**
   * Open `schemas/app-config.schema.json` and the contract test for the module actually under test — `<infra-repo>/iac/aws-epam-ecs-app/tests/app.tftest.hcl`. (The bundled `tests/tftests/*.tftest.hcl` are templates: that directory holds no `.tf`, so Layer 2 does not execute there. The terminal will name the real module — `Layer 2: ... in: aws-epam-ecs-app` — so open the matching file or the audience will spot the mismatch.)
   * *"This contract defines our exact requirements: IAM boundary, health probes, ALB priority, and port routing."*

---

### Act 2: The Initial Failure (The Red Badge) — 1.5 Minutes
1. **Trigger an intentional failure scenario:**
   * In `deploy/dev/config.yaml`, set an out-of-range container `PORT`, an invalid `CPU`/`MEMORY` pairing, or remove the `health_check` path.
   * **Do not seed an ALB priority collision here.** Cross-service routing conflicts exit `2` with a 🟣 ESCALATION at Layer 1 and deliberately stop the self-healing loop — correct behaviour, but it ends this act early. That path has its own act below.
2. **Run the Orchestrator:**
   ```bash
   uv run scripts/tdd_orchestrator.py --config deploy/dev/config.yaml --specs-dir Project_Specifications/
   ```
3. **Point to the terminal:**
   * Discovery step automatically locates local PC architecture specs:
     `🔍 Discovered additional local specifications at: .../Project_Specifications`
   * Large red badge appears: `🔴 [RED PHASE: SPECIFICATION VIOLATION / ASSERTION FAILED]`
   * Highlight to the audience: *"In traditional workflows, you'd find this out 20 minutes into deployment or in a staging incident. Here, our Python runner caught it in 1.4 seconds."*

---

### Act 3: Claude Enters the Loop (Self-Healing in Real Time) — 2.5 Minutes
1. **Prompt Claude Code:**
   > *"Run the platform-ops TDD orchestrator on `zippo-certs`. Cross-reference local specifications in `Project_Specifications/`, analyze the failure, heal the configuration to satisfy all contract rules, and repeat until green."*
2. **Audience watches Claude's thought process:**
   * Claude reads the `DIAGNOSTIC:` block emitted by the Python orchestrator — `failure_class`, `disposition`, and `remediation` are stated explicitly, so there is no guesswork to narrate.
   * Claude checks local architectural specs (`04_APPLICATION_DEPLOYMENT_CONFIG.md` for sizing and port baselines).
   * Claude identifies the root cause (e.g., *"`PORT: 99999` exceeds the maximum of 65535; the spec baseline for this service family is 3000"*).
   * Claude edits `config.yaml` or the Terraform wrapper.
   * Claude triggers the orchestrator runner automatically.
   * **Worth calling out to the audience:** the `disposition` field is what keeps this honest. `RED` means a real defect Claude may fix. `BLOCKED` means the layer never ran, so Claude fixes the environment instead of editing code that was never shown to be wrong.

---

### Act 3b: The Line Claude Will Not Cross (Escalation) — 1.5 Minutes

*The most valuable 90 seconds of the demo: the loop declining to self-heal.*

1. **Seed a routing conflict** — give the new service the catch-all already owned by the frontend:
   ```yaml
   ALB:
     path_patterns: ["/*"]     # already owned by zippo-fe
     priority: 100             # already held by zippo-fe
   ```
2. **Re-run the orchestrator.** It stops at Layer 1, before any test executes:
   ```
   [*] Phase: Layer 1: Cross-Service ALB Ingress Collision Check...

   🟣 [ESCALATION: HUMAN DECISION REQUIRED] (0.31s)

   [1] HARD - DUPLICATE_PRIORITY
       conflicts with: frontend  (.../ZIPPO-FE/deploy/dev/config.yaml)
       consequence:    both services declare ALB.priority 100 on the shared
                       listener; AWS rejects the second apply with PriorityInUse

   OPTIONS - REQUIRES HUMAN DECISION, DO NOT SELECT ONE AUTONOMOUSLY
     A) COEXIST   - move this service to its own route
     B) REPLACE   - DECOMMISSIONS frontend; existing URLs break
     C) COEXIST, INVERTED - the peer moves instead
     D) DEFER     - change nothing
   ```
3. **Prompt Claude with the same self-healing instruction as Act 3** — *"heal the configuration and repeat until green."*
4. **Claude refuses, and says why.** It relays the four options and stops. It does not pick a free priority to reach green.
5. **The punchline for the audience:**
   * *"Every other failure in this demo, Claude fixed by itself. This one it will not touch — and that is the feature. There was a priority available. Taking it would have turned the pipeline green and silently taken the frontend offline, because a catch-all can only have one owner. Green is not the goal. Correct is."*
   * *"Exit code 2 is a distinct contract: not 'pass', not 'fail', but 'this decision is not mine to make'."*

---

### Act 4: The Green Phase (Mission Accomplished) — 1 Minute
1. **Terminal displays:**
   ```
   ══════════════════════════════════════════════════════════════════════
               AI-DRIVEN IAC ORCHESTRATOR: TDD LOOP
   ══════════════════════════════════════════════════════════════════════
   [*] Phase: Checking for Additional Local Specifications...
     🔍 Discovered additional local specifications at: .../Project_Specifications
     Found 11 local specification document(s):
       • 00_ARCHITECTURE_OVERVIEW.md
       • 01_NAMING_CONVENTIONS.md
       • 04_APPLICATION_DEPLOYMENT_CONFIG.md
       • 09_NETWORKING_AND_INGRESS.md
       ...
     ✓ Local specifications loaded and checked for architecture constraints.

   [*] Phase: Layer 1: Validating Specification (config.yaml)...
     ✓ Schema Contract: Valid (100% compliant with JSON Schema)
   [*] Phase: Layer 1: Cross-Service ALB Ingress Collision Check...
     ✓ ALB Ingress: no priority or path-pattern collision with peers
   [*] Phase: Layer 1: Terraform Format & Syntax Validation in dev...
     ✓ Terraform Format: Clean (HCL canonical style)
     ✓ Terraform Validate: Syntax & configuration valid
   [*] Phase: Layer 2: Executing Native Contract Unit Tests in: aws-epam-ecs-app...
     ✓ Contract Assertions: 23 passed, 0 failed
   [*] Phase: Layer 3: Verifying Terraform Plan in dev...
     ✓ Plan Preview: 14 to add, 0 to change, 0 to destroy.

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED] (1.82s)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Summary: 23 Passed, 0 Failed, 0 Skipped.
   Verified: Layer 1 (schema + ingress), Layer 1 (terraform fmt/validate), Layer 2 (contract tests), Layer 3 (plan preview)
   Ready for continuous deployment pipeline (ECR Release & TF Apply).
   ```
2. **⚠ Presenter pre-flight — this is the act most likely to embarrass you.**
   A true 🟢 requires **all three** layers to actually run. Layer 1 `validate` and Layer 3 `plan` need `terraform init` in the deploy directory *and* live AWS credentials. Without them you will get 🟡 **PARTIAL** instead:
   ```
   🟡 [PARTIAL: CONTRACT TESTS PASSED, COVERAGE INCOMPLETE]
   NOT verified:
     ⚠ Layer 3 plan: NOT RUN - blocked by NOT_INITIALIZED
   ```
   That is the orchestrator being honest, not broken. Before presenting, verify end-to-end:
   ```bash
   terraform -chdir=<deploy-dir> init
   aws sts get-caller-identity        # must succeed
   uv run scripts/tdd_orchestrator.py --config <deploy-dir>/config.yaml   # expect exit 0 + 🟢
   ```
   If you cannot get credentials on the demo machine, present 🟡 PARTIAL as the intended finish and make *that* the point — see the closing note below.
3. **Closing punchline for the audience:**
   * *"Zero lines of manual boilerplate written. Zero guesswork. The AI operated within strict guardrails, failed safely, fixed itself, and produced verified, compliant IaC."*
   * If you finished on 🟡 PARTIAL, close on this instead — it is the stronger message: *"Notice what it refused to do. It passed 23 contract assertions and still would not call the job done, because one layer never ran. A tool that reports green when it only checked two of three layers is worse than no tool at all."*
