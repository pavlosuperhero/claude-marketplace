#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
TDD IaC Orchestrator & Live Demo Test Runner
Executes the Red-Green-Refactor loop:
  1. Validates declarative config against JSON Schema (using uv / pyyaml)
  2. Runs the selected native Terraform contract test suite
  3. Formats presentation-friendly RED / GREEN output for human audience & AI self-healing

CLI Usage:
  uv run scripts/tdd_orchestrator.py --config /path/to/config.yaml --infra-dir /path/to/infra/module
  # Or via environment variables:
  INFRA_REPO_PATH=/path/to/infra uv run scripts/tdd_orchestrator.py --config /path/to/config.yaml
"""

import sys
import os
import subprocess
import time
import re
import argparse
from pathlib import Path

from platform_ops_paths import PLUGIN_ROOT, add_specs_argument, find_specs_dir

# ANSI Color Codes for terminal presentation
BOLD = "\033[1m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
RESET = "\033[0m"

def print_banner(title):
    width = 70
    print(f"\n{CYAN}{'═' * width}{RESET}")
    print(f"{BOLD}{title.center(width)}{RESET}")
    print(f"{CYAN}{'═' * width}{RESET}\n")

def run_step(step_name):
    print(f"{BOLD}[*] Phase: {step_name}...{RESET}")

# Stable exit-code contract, shared with tests/check_ingress_collisions.py.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ESCALATE = 2
EXIT_PARTIAL = 3

APP_CONTRACT = "app_contract.tftest.hcl"

# Synthetic returncodes for failures that happen before a tool produces output.
TOOL_MISSING = 127
TOOL_TIMEOUT = 124


def run_tool(cmd, env=None, timeout=900, cwd=None):
    """
    Run an external tool without ever raising.

    Returns (returncode, combined_output, harness_error). harness_error is set only
    when the tool could not be executed at all - missing binary, timeout, OS refusal.
    That is deliberately distinct from "the tool ran and reported failure": the
    remediation differs, and an agent reading this output must be able to tell them
    apart rather than guessing from a returncode alone.
    """
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=env, cwd=cwd, timeout=timeout
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), None
    except FileNotFoundError:
        return TOOL_MISSING, "", f"executable not found on PATH: '{cmd[0]}'"
    except subprocess.TimeoutExpired:
        return TOOL_TIMEOUT, "", f"'{' '.join(cmd)}' exceeded the {timeout}s timeout"
    except PermissionError as e:
        return TOOL_MISSING, "", f"permission denied executing '{cmd[0]}': {e}"
    except OSError as e:
        return TOOL_MISSING, "", f"OS error executing '{cmd[0]}': {e}"


# Ordered most-specific-first: the first matching class wins, so a credentials error
# is never misreported as a generic "run terraform init".
PLAN_FAILURE_CLASSES = [
    (
        "INGRESS_CONFLICT", "ESCALATE",
        [r"PriorityInUse", r"DuplicateListener", r"Priority '\d+' is currently in use"],
        "An ALB listener rule priority is already taken by another service. This is a "
        "routing ownership conflict, NOT a formatting problem. Run "
        "tests/check_ingress_collisions.py and escalate the options to the human. "
        "Do NOT pick a new priority yourself.",
    ),
    (
        # 'terraform test' resolves mock_provider against the required_providers of the
        # configuration in the test directory. No .tf there means nothing to bind to, and
        # 'terraform init' does NOT fix it - so this must not be classed as NOT_INITIALIZED.
        "NO_CONFIG_UNDER_TEST", "RED",
        [r"unknown provider registry", r"unknown provider \""],
        "A .tftest.hcl declares mock_provider for a provider that the configuration "
        "under test does not declare in required_providers. Usually the test directory "
        "contains no .tf configuration at all. Point --infra-dir at the real Terraform "
        "module (the directory holding main.tf/variables.tf), or add the missing "
        "required_providers there. Running 'terraform init' will NOT fix this.",
    ),
    (
        "NOT_INITIALIZED", "BLOCKED",
        # Terraform wraps these messages across lines, so \s+ spans the newline.
        [r'run\s+"?terraform init', r"module is not yet installed",
         r"Module source has changed", r"to install all modules",
         r"Module not installed", r"Missing required provider",
         r"Initialization required", r"provider registry.*could not",
         r"Backend initialization required"],
        "The working directory has no initialized providers or modules. Run "
        "'terraform -chdir=<dir> init' for the directory named in 'command' above, then "
        "re-run. This layer proved NOTHING in this run - do not report it as verified.",
    ),
    (
        "MISSING_CREDENTIALS", "BLOCKED",
        [r"No valid credential sources", r"NoCredentialProviders",
         r"failed to refresh cached credentials", r"InvalidClientTokenId",
         r"ExpiredToken", r"UnrecognizedClientException", r"AuthFailure",
         r"could not be found or.*credentials"],
        "AWS credentials are absent or expired. Authenticate, then re-run. "
        "Layer 3 proved NOTHING in this run - do not report the plan as verified.",
    ),
    (
        "STATE_BACKEND_ERROR", "BLOCKED",
        [r"Error refreshing state", r"error loading state",
         r"Failed to get existing workspaces", r"Error acquiring the state lock"],
        "The remote state backend is unreachable or locked. Verify backend config and "
        "that no other apply holds the lock. Layer 3 proved NOTHING in this run.",
    ),
    (
        "INSUFFICIENT_PERMISSIONS", "RED",
        [r"AccessDenied", r"UnauthorizedOperation", r"is not authorized to perform"],
        "The authenticated principal lacks IAM permissions the plan needs. This is a "
        "real defect in the IAM boundary - report the exact denied action to the human.",
    ),
    (
        "CONFIG_ERROR", "RED",
        [r"Unsupported argument", r"Reference to undeclared",
         r"Missing required argument", r"Invalid value for", r"Unsupported block type",
         r"Invalid reference", r"No value for required variable"],
        "The Terraform configuration itself is invalid. Read the Error: lines above, "
        "patch the offending .tf or config.yaml, and re-run.",
    ),
]


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def classify_failure(output, classes=PLAN_FAILURE_CLASSES):
    """
    Map tool output to (class_name, disposition, remediation) deterministically.

    Colour codes are stripped before matching - Terraform emits them even when the
    caller forgets -no-color, and they otherwise split signature phrases apart.

    Returns ("UNCLASSIFIED", "RED", ...) when nothing matches - an unknown failure is
    surfaced as RED, never as success. Silence is not a pass.
    """
    clean = ANSI_ESCAPE.sub("", output)
    for name, disposition, patterns, remediation in classes:
        for pattern in patterns:
            if re.search(pattern, clean, re.IGNORECASE):
                return name, disposition, remediation
    return (
        "UNCLASSIFIED", "RED",
        "This failure matches no known signature. Read the raw output above verbatim "
        "and diagnose it directly - do not assume it is benign.",
    )


def print_clue_block(title, tool_class, disposition, remediation, cmd, output, error=None):
    """Emit a uniform, greppable diagnostic block. Deterministic field order."""
    print(f"\n{YELLOW}{'─' * 70}{RESET}")
    print(f"{BOLD}DIAGNOSTIC: {title}{RESET}")
    print(f"{YELLOW}{'─' * 70}{RESET}")
    print(f"  failure_class: {tool_class}")
    print(f"  disposition:   {disposition}")
    print(f"  command:       {' '.join(cmd)}")
    if error:
        print(f"  harness_error: {error}")
    print(f"  remediation:   {remediation}")
    if output.strip():
        print(f"\n{BOLD}  Raw tool output:{RESET}")
        for line in output.strip().splitlines():
            print(f"    │ {line}")
    print(f"{YELLOW}{'─' * 70}{RESET}\n")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the TDD IaC Orchestrator against an application config and Terraform module."
    )
    parser.add_argument(
        "-c", "--config",
        dest="config_path",
        default=os.environ.get("APP_CONFIG_PATH"),
        help="Path to the application deployment config.yaml to validate (or env APP_CONFIG_PATH)."
    )
    parser.add_argument(
        "-i", "--infra-dir",
        dest="infra_dir",
        default=os.environ.get("INFRA_REPO_PATH"),
        help="Path to the Terraform module containing the contract tests (or env INFRA_REPO_PATH)."
    )
    parser.add_argument(
        "-s", "--schema",
        dest="schema_path",
        default=os.environ.get("APP_SCHEMA_PATH"),
        help="Custom path to the app-config JSON schema (or env APP_SCHEMA_PATH)."
    )
    parser.add_argument(
        "--contract-test", default=os.environ.get("CONTRACT_TEST_PATH"),
        help=f"Terraform test file relative to --infra-dir (default: tests/{APP_CONTRACT}, then {APP_CONTRACT}).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 3 when verification is incomplete.")
    add_specs_argument(parser)
    return parser.parse_args()

def has_terraform_config(directory):
    return directory.is_dir() and any(
        path.is_file() and path.name.endswith((".tf", ".tf.json")) for path in directory.iterdir()
    )


def find_contract_test(infra_dir, configured):
    candidates = [Path(configured)] if configured else [Path("tests") / APP_CONTRACT, Path(APP_CONTRACT)]
    for path in candidates:
        if path.is_absolute() or not path.name.endswith((".tftest.hcl", ".tftest.json")):
            continue
        candidate = (infra_dir / path).resolve()
        if candidate.is_relative_to(infra_dir) and candidate.is_file():
            return candidate.relative_to(infra_dir)
    return None


def main():
    args = parse_args()
    if not args.infra_dir:
        print(f"{RED}Error: Pass --infra-dir or set INFRA_REPO_PATH to the Terraform module directory.{RESET}",
              file=sys.stderr)
        sys.exit(EXIT_ERROR)

    infra_dir = Path(args.infra_dir).expanduser().resolve()
    if not has_terraform_config(infra_dir):
        print(f"{RED}Error: No Terraform configuration (.tf or .tf.json files) in {infra_dir}.{RESET}",
              file=sys.stderr)
        sys.exit(EXIT_ERROR)

    validator_script = PLUGIN_ROOT / "tests/validate_configs.py"
    schema_path = Path(args.schema_path).expanduser() if args.schema_path else PLUGIN_ROOT / "schemas/app-config.schema.json"

    print_banner("AI-DRIVEN IAC ORCHESTRATOR: TDD LOOP")
    start_time = time.time()

    # ─────────────────────────────────────────────────────────────
    # STAGE 0: Check for Additional Local Specifications
    # ─────────────────────────────────────────────────────────────
    specs_dir = find_specs_dir(args.specs_dir)

    run_step("Checking for Additional Local Specifications")
    if specs_dir and os.path.isdir(specs_dir):
        spec_docs = sorted([f for f in os.listdir(specs_dir) if f.endswith(".md") or f.endswith(".json") or f.endswith(".yaml")])
        print(f"  {CYAN}🔍 Discovered additional local specifications at:{RESET} {specs_dir}")
        print(f"  Found {len(spec_docs)} local specification document(s):")
        for doc in spec_docs[:6]:
            print(f"    • {doc}")
        if len(spec_docs) > 6:
            print(f"    • ... and {len(spec_docs) - 6} more documents")
        print(f"{GREEN}  ✓ Local specifications available for architecture review.{RESET}\n")
    elif specs_dir and not os.path.exists(specs_dir):
        print(f"  {YELLOW}⚠ Specified local specs path not found: {specs_dir}{RESET}\n")
    else:
        print(f"  {CYAN}ℹ No additional local specs directory specified (using standard baseline).{RESET}")
        print(f"  {CYAN}  Tip: Pass --specs-dir /path/to/specs or set ADDITIONAL_SPECS_PATH to load local project docs.{RESET}\n")

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: Layer 1 - Static Analysis & Schema Contract
    # ─────────────────────────────────────────────────────────────
    # Per-layer verdicts. These drive the final summary so it can never claim
    # coverage for a layer that was skipped or blocked.
    ingress_verified = False
    layer1_tf_status = "NOT RUN"
    layer3_status = "NOT RUN"
    layer3_reason = "no .tf files found in the deploy directory"

    deploy_dir = None
    if args.config_path:
        if not os.path.exists(args.config_path):
            print(f"{RED}Error: Config file not found at: {args.config_path}{RESET}")
            sys.exit(1)

        deploy_dir = os.path.dirname(os.path.abspath(args.config_path))
        run_step(f"Layer 1: Validating Specification ({os.path.basename(args.config_path)})")
        val_cmd = ["uv", "run", str(validator_script), "--config", args.config_path,
                   "--schema", str(schema_path)]
        if specs_dir:
            val_cmd.extend(["--specs-dir", str(specs_dir)])
        val_rc, val_out, val_err = run_tool(val_cmd, timeout=120)
        if val_err:
            print_clue_block(
                "Layer 1 - config validator could not run", "TOOL_UNAVAILABLE", "BLOCKED",
                "Check uv, the validator path, and the tool timeout before re-running.",
                val_cmd, val_out, val_err,
            )
            sys.exit(EXIT_ERROR)

        if val_rc != EXIT_OK:
            elapsed = time.time() - start_time
            print(f"\n{RED}{'━' * 70}{RESET}")
            print(f"{RED}🔴 [RED PHASE: SPECIFICATION VIOLATION DETECTED]{RESET} ({elapsed:.2f}s)")
            print(f"{RED}{'━' * 70}{RESET}")
            print(f"{YELLOW}Actionable Diagnostics for LLM Self-Healing:{RESET}\n")
            print(val_out)
            print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
            print("Analyze the schema violation above, patch the invalid properties in config.yaml, and re-run the orchestrator.\n")
            sys.exit(1)
        else:
            print(f"{GREEN}  ✓ Schema Contract: Valid (100% compliant with JSON Schema){RESET}")

        # ── Layer 1b: cross-service ALB ingress collision ──────────────
        # The JSON Schema documents that ALB.priority must be unique across services
        # sharing the ALB, but a single-file check cannot see peers. This closes that gap.
        run_step("Layer 1: Cross-Service ALB Ingress Collision Check")
        collision_script = str(PLUGIN_ROOT / "tests/check_ingress_collisions.py")
        if not os.path.exists(collision_script):
            print(f"{YELLOW}  ⚠ Collision checker missing at {collision_script}{RESET}")
            print(f"{YELLOW}    Ingress uniqueness was NOT verified in this run.{RESET}")
        else:
            col_cmd = ["uv", "run", collision_script, "--config", args.config_path, "--require-peers"]
            col_rc, col_out, col_err = run_tool(col_cmd, timeout=120)

            if col_err:
                print(f"{YELLOW}  ⚠ Could not run the ingress collision check: {col_err}{RESET}")
                print(f"{YELLOW}    Ingress uniqueness was NOT verified in this run.{RESET}")
            elif col_rc == EXIT_ESCALATE:
                elapsed = time.time() - start_time
                print(f"\n{MAGENTA}{'━' * 70}{RESET}")
                print(f"{MAGENTA}🟣 [ESCALATION: HUMAN DECISION REQUIRED]{RESET} ({elapsed:.2f}s)")
                print(f"{MAGENTA}{'━' * 70}{RESET}")
                print(col_out)
                print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
                print("This is NOT a self-healing failure. Do not edit any config.yaml to")
                print("resolve it. Relay the conflict and the enumerated options to the human,")
                print("then stop and wait for an explicit choice.\n")
                sys.exit(EXIT_ESCALATE)
            elif col_rc != EXIT_OK:
                print(f"{YELLOW}  ⚠ Ingress collision check errored (exit {col_rc}):{RESET}")
                print(col_out)
                print(f"{YELLOW}    Ingress uniqueness was NOT verified in this run.{RESET}")
            else:
                ingress_verified = True
                print(col_out, end="" if col_out.endswith("\n") else "\n")

    # Check Terraform formatting & validation if .tf files exist in deploy/
    has_deploy_config = deploy_dir is not None and has_terraform_config(Path(deploy_dir))
    env = os.environ.copy()
    env["TF_CLI_CONFIG_FILE"] = "/dev/null"
    if has_deploy_config:
        layer1_tf_status = "VERIFIED"
        run_step(f"Layer 1: Terraform Format & Syntax Validation in {os.path.basename(deploy_dir)}")
        fmt_cmd = ["terraform", f"-chdir={deploy_dir}", "fmt", "-check"]
        fmt_rc, fmt_out, fmt_err = run_tool(fmt_cmd, env=env, timeout=120)
        if fmt_err:
            print_clue_block(
                "Layer 1 - terraform fmt could not run", "TOOL_UNAVAILABLE", "BLOCKED",
                "Install Terraform or add it to PATH. Formatting was NOT checked.",
                fmt_cmd, fmt_out, fmt_err,
            )
        elif fmt_rc != 0:
            print(f"{YELLOW}  ⚠ Unformatted Terraform files detected. Auto-formatting with 'terraform fmt'...{RESET}")
            run_tool(["terraform", f"-chdir={deploy_dir}", "fmt"], env=env, timeout=120)
            print(f"{GREEN}  ✓ Formatted HCL files in {os.path.basename(deploy_dir)}{RESET}")
        else:
            print(f"{GREEN}  ✓ Terraform Format: Clean (HCL canonical style){RESET}")

        val_cmd_tf = ["terraform", f"-chdir={deploy_dir}", "validate", "-no-color"]
        val_rc, val_out, val_tool_err = run_tool(val_cmd_tf, env=env, timeout=300)
        if val_rc == 0 and not val_tool_err:
            print(f"{GREEN}  ✓ Terraform Validate: Syntax & configuration valid{RESET}")
        else:
            # Previously this branch was absent entirely, so a failed validate passed
            # silently into a GREEN verdict. Classify it and act on the disposition.
            v_class, v_disp, v_fix = classify_failure(val_out)
            if val_tool_err:
                v_class, v_disp, v_fix = ("TOOL_UNAVAILABLE", "BLOCKED",
                                          "Install Terraform or add it to PATH. "
                                          "Validation was NOT performed.")
            print_clue_block(
                "Layer 1 - terraform validate failed", v_class, v_disp, v_fix,
                val_cmd_tf, val_out, val_tool_err,
            )
            if v_disp == "RED":
                elapsed = time.time() - start_time
                print(f"{RED}{'━' * 70}{RESET}")
                print(f"{RED}🔴 [RED PHASE: TERRAFORM CONFIGURATION INVALID]{RESET} ({elapsed:.2f}s)")
                print(f"{RED}{'━' * 70}{RESET}")
                print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
                print("Patch the Terraform configuration per the remediation above, then re-run.\n")
                sys.exit(EXIT_ERROR)
            layer1_tf_status = f"NOT VERIFIED ({v_class})"

    # ─────────────────────────────────────────────────────────────
    # STAGE 2: Layer 2 - Native Terraform Contract Tests (TDD)
    # ─────────────────────────────────────────────────────────────
    run_step(f"Layer 2: Executing Native Contract Unit Tests in: {os.path.basename(infra_dir)}")
    
    contract_test = find_contract_test(infra_dir, args.contract_test)
    if contract_test is None:
        print_clue_block(
            "Layer 2 - required contract test file not found", "CONTRACT_TEST_NOT_FOUND", "BLOCKED",
            f"Place {APP_CONTRACT} in the module or its tests/ directory, or set --contract-test "
            "to a .tftest.hcl or .tftest.json file inside --infra-dir.",
            ["terraform", f"-chdir={infra_dir}", "test"], args.contract_test or "",
        )
        sys.exit(EXIT_ERROR)

    tf_cmd = ["terraform", f"-chdir={infra_dir}", "test", "-no-color", f"-filter={contract_test}"]
    if contract_test.parent != Path("."):
        tf_cmd.append(f"-test-directory={contract_test.parent}")
    tf_rc, output, tf_tool_err = run_tool(tf_cmd, env=env, timeout=900)

    # Parse results from output
    m_pass = re.search(r"(\d+)\s+passed", output)
    passes = int(m_pass.group(1)) if m_pass else len(re.findall(r"\.\.\.\s*pass", output))

    m_fail = re.search(r"(\d+)\s+failed", output)
    fails = int(m_fail.group(1)) if m_fail else len(re.findall(r"\.\.\.\s*fail", output))

    m_skip = re.search(r"(\d+)\s+skipped", output)
    skips = int(m_skip.group(1)) if m_skip else len(re.findall(r"\.\.\.\s*skip", output))

    if tf_rc == 0 and passes == 0 and fails == 0:
        print_clue_block(
            "Layer 2 - no contract assertions ran", "NO_TEST_RESULTS", "BLOCKED",
            "Point --infra-dir at a module with runnable Terraform contract tests.",
            tf_cmd, output, tf_tool_err,
        )
        sys.exit(EXIT_ERROR)

    if tf_rc != 0 or fails > 0 or tf_tool_err:
        elapsed = time.time() - start_time

        # Distinguish "assertions genuinely failed" from "the test harness never ran".
        # Telling an agent to self-heal manifests when the real cause is a missing
        # 'terraform init' sends it editing correct code - the worst kind of bad clue.
        t_class, t_disp, t_fix = classify_failure(output)
        if tf_tool_err:
            t_class, t_disp, t_fix = ("TOOL_UNAVAILABLE", "BLOCKED",
                                      "Install Terraform or add it to PATH. "
                                      "No contract test was executed.")
        harness_blocked = fails == 0 and passes == 0 and (tf_tool_err or t_disp == "BLOCKED")

        if harness_blocked:
            print(f"\n{YELLOW}{'━' * 70}{RESET}")
            print(f"{YELLOW}🟡 [LAYER 2 BLOCKED: CONTRACT TESTS NEVER EXECUTED]{RESET} ({elapsed:.2f}s)")
            print(f"{YELLOW}{'━' * 70}{RESET}")
            print_clue_block(
                f"Layer 2 - test harness could not run in {os.path.basename(infra_dir)}",
                t_class, t_disp, t_fix, tf_cmd, output, tf_tool_err,
            )
            print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
            print("Do NOT edit manifests or config.yaml - zero assertions ran, so nothing has")
            print("been shown to be wrong. Fix the environment first, then re-run:")
            print(f"  terraform -chdir={infra_dir} init")
            print("Report to the human that Layer 2 did not execute.\n")
            sys.exit(EXIT_ERROR)

        print(f"\n{RED}{'━' * 70}{RESET}")
        print(f"{RED}🔴 [RED PHASE: TEST ASSERTION FAILURES DETECTED]{RESET} ({elapsed:.2f}s)")
        print(f"{RED}{'━' * 70}{RESET}")
        print(f"{YELLOW}Failed Assertions: {fails} | Passed: {passes} | Skipped: {skips}{RESET}\n")

        # Extract specific error messages
        print(f"{BOLD}Diagnostic Output:{RESET}")
        for line in output.splitlines():
            if any(k in line for k in ["fail", "Error:", "error_message", "Error while"]):
                print(f"  {RED}✖ {line.strip()}{RESET}")
            elif "run " in line:
                print(f"  • {line.strip()}")

        if t_class == "INGRESS_CONFLICT":
            print(f"\n{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
            print(f"{t_fix}\n")
            sys.exit(EXIT_ESCALATE)

        print(f"\n{BOLD}Detected failure class:{RESET} {t_class} ({t_disp})")
        print(f"{BOLD}Remediation:{RESET} {t_fix}")
        print(f"\n{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
        print("Read the failed assertions above. Self-heal the Terraform manifests or config.yaml to satisfy all conditions, then re-test.\n")
        sys.exit(EXIT_ERROR)
    else:
        print(f"{GREEN}  ✓ Contract Assertions: {passes} passed, 0 failed{RESET}")

    # ─────────────────────────────────────────────────────────────
    # STAGE 3: Layer 3 - Plan Verification (Dry-Run Preview)
    # ─────────────────────────────────────────────────────────────
    if has_deploy_config:
        run_step(f"Layer 3: Verifying Terraform Plan in {os.path.basename(deploy_dir)}")
        plan_cmd = ["terraform", f"-chdir={deploy_dir}", "plan", "-no-color",
                    "-input=false", "-detailed-exitcode"]
        plan_rc, plan_out, plan_tool_err = run_tool(plan_cmd, env=env, timeout=900)

        m_plan = re.search(
            r"Plan:\s+(\d+)\s+to add,\s+(\d+)\s+to change,\s+(\d+)\s+to destroy", plan_out
        )
        if not plan_tool_err and plan_rc in (0, 2):
            if plan_rc == 0:
                summary = "Infrastructure up to date (0 changes)."
            elif m_plan:
                adds, changes, destroys = m_plan.groups()
                summary = f"{adds} to add, {changes} to change, {destroys} to destroy."
            else:
                summary = "Changes detected. See the plan output for details."
            print(f"{GREEN}  ✓ Plan Preview: {summary}{RESET}")
            if plan_rc == 2 and not m_plan:
                print(plan_out)
            layer3_status = "VERIFIED"
        else:
            p_class, p_disp, p_fix = classify_failure(plan_out)
            if plan_tool_err:
                p_class, p_disp, p_fix = ("TOOL_UNAVAILABLE", "BLOCKED",
                                          "Install Terraform or add it to PATH. "
                                          "The plan was NOT previewed.")
            print_clue_block(
                "Layer 3 - terraform plan did not produce a verified preview",
                p_class, p_disp, p_fix, plan_cmd, plan_out, plan_tool_err,
            )
            layer3_status = "NOT RUN"
            layer3_reason = f"blocked by {p_class}"

            if p_disp == "ESCALATE":
                elapsed = time.time() - start_time
                print(f"{MAGENTA}{'━' * 70}{RESET}")
                print(f"{MAGENTA}🟣 [ESCALATION: HUMAN DECISION REQUIRED]{RESET} ({elapsed:.2f}s)")
                print(f"{MAGENTA}{'━' * 70}{RESET}")
                print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
                print("Run tests/check_ingress_collisions.py, relay its options to the human,")
                print("and stop. Do not reassign priorities or path patterns yourself.\n")
                sys.exit(EXIT_ESCALATE)
            if p_disp == "RED":
                elapsed = time.time() - start_time
                print(f"{RED}{'━' * 70}{RESET}")
                print(f"{RED}🔴 [RED PHASE: PLAN VERIFICATION FAILED]{RESET} ({elapsed:.2f}s)")
                print(f"{RED}{'━' * 70}{RESET}")
                print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
                print("Apply the remediation above, then re-run the orchestrator.\n")
                sys.exit(EXIT_ERROR)

    # ─────────────────────────────────────────────────────────────
    # FINAL VERDICT - reports only the layers that actually ran
    # ─────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    verified = []
    unverified = []
    if args.config_path:
        verified.append("Layer 1 (schema)")
        if ingress_verified:
            verified.append("Layer 1 (ingress)")
        else:
            unverified.append("Layer 1 ingress: NOT VERIFIED")
    if layer1_tf_status == "VERIFIED" and deploy_dir:
        verified.append("Layer 1 (terraform fmt/validate)")
    else:
        unverified.append(f"Layer 1 terraform: {layer1_tf_status}")
    if skips:
        unverified.append(f"Layer 2 contract tests: {skips} skipped")
    else:
        verified.append("Layer 2 (contract tests)")
    if layer3_status == "VERIFIED":
        verified.append("Layer 3 (plan preview)")
    else:
        unverified.append(f"Layer 3 plan: {layer3_status} - {layer3_reason}")

    if unverified:
        print(f"\n{YELLOW}{'━' * 70}{RESET}")
        print(f"{YELLOW}🟡 [PARTIAL: CONTRACT TESTS PASSED, COVERAGE INCOMPLETE]{RESET} ({elapsed:.2f}s)")
        print(f"{YELLOW}{'━' * 70}{RESET}")
        print(f"{BOLD}Verified:{RESET} {GREEN}{', '.join(verified)}{RESET}")
        print(f"{BOLD}NOT verified:{RESET}")
        for u in unverified:
            print(f"  {YELLOW}⚠ {u}{RESET}")
        print(f"\n{BOLD}Assertions:{RESET} {passes} passed, 0 failed, {skips} skipped.")
        print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
        print("Do NOT report this run as fully verified. State explicitly which layers did")
        print("not run and why, using the diagnostic blocks above. This is not deploy-ready")
        print("until every layer above is verified.\n")
        sys.exit(EXIT_PARTIAL if args.strict else EXIT_OK)

    print(f"\n{GREEN}{'━' * 70}{RESET}")
    print(f"{GREEN}🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]{RESET} ({elapsed:.2f}s)")
    print(f"{GREEN}{'━' * 70}{RESET}")
    print(f"{BOLD}Summary:{RESET} {GREEN}{passes} Passed{RESET}, 0 Failed, {skips} Skipped.")
    print(f"{BOLD}Verified:{RESET} {GREEN}{', '.join(verified)}{RESET}")
    print(f"{CYAN}Ready for continuous deployment pipeline (ECR Release & TF Apply).{RESET}\n")
    sys.exit(EXIT_OK)

if __name__ == "__main__":
    main()
