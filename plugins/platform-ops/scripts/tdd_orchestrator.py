#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
TDD IaC Orchestrator & Live Demo Test Runner
Executes the Red-Green-Refactor loop:
  1. Validates declarative config against JSON Schema (using uv / pyyaml)
  2. Runs native Terraform contract tests (*.tftest.hcl) in mock mode
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
        help="Path to the Terraform infrastructure module or test directory (or env INFRA_REPO_PATH)."
    )
    parser.add_argument(
        "-s", "--schema",
        dest="schema_path",
        default=None,
        help="Custom path to the app-config JSON schema (optional)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Resolve infra directory
    infra_dir = args.infra_dir
    if not infra_dir:
        # Check standard relative search locations if not provided
        candidates = [
            os.path.abspath(os.path.join(plugin_dir, "tests/tftests")),
            os.path.abspath(os.path.join(plugin_dir, "../../../ZIPPO-INFR/iac/aws-epam-ecs-app")),
            os.path.abspath(os.path.join(plugin_dir, "../../ZIPPO-INFR/iac/aws-epam-ecs-app")),
        ]
        for c in candidates:
            if os.path.exists(c):
                infra_dir = c
                break

    if not infra_dir or not os.path.exists(infra_dir):
        print(f"{RED}Error: Infrastructure directory not specified or does not exist.{RESET}")
        print("Please pass --infra-dir /path/to/module or set INFRA_REPO_PATH environment variable.")
        sys.exit(1)

    validator_script = os.path.join(plugin_dir, "tests/validate_configs.py")
    schema_path = args.schema_path or os.path.join(plugin_dir, "schemas/app-config.schema.json")

    print_banner("AI-DRIVEN IAC ORCHESTRATOR: TDD LOOP")
    start_time = time.time()

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: Schema Contract Validation (SDD)
    # ─────────────────────────────────────────────────────────────
    if args.config_path:
        if not os.path.exists(args.config_path):
            print(f"{RED}Error: Config file not found at: {args.config_path}{RESET}")
            sys.exit(1)

        run_step(f"Validating Specification ({os.path.basename(args.config_path)})")
        val_cmd = ["uv", "run", validator_script, "--config", args.config_path, "--schema", schema_path]
        proc = subprocess.run(val_cmd, capture_output=True, text=True)
        
        if proc.returncode != 0:
            elapsed = time.time() - start_time
            print(f"\n{RED}{'━' * 70}{RESET}")
            print(f"{RED}🔴 [RED PHASE: SPECIFICATION VIOLATION DETECTED]{RESET} ({elapsed:.2f}s)")
            print(f"{RED}{'━' * 70}{RESET}")
            print(f"{YELLOW}Actionable Diagnostics for LLM Self-Healing:{RESET}\n")
            print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
            print(f"{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
            print("Analyze the schema violation above, patch the invalid properties in config.yaml, and re-run the orchestrator.\n")
            sys.exit(1)
        else:
            print(f"{GREEN}  ✓ Schema Contract: Valid (100% compliant with JSON Schema){RESET}")

    # ─────────────────────────────────────────────────────────────
    # STAGE 2: Native Terraform Contract Tests (TDD)
    # ─────────────────────────────────────────────────────────────
    run_step(f"Executing Native Terraform Contract Tests in: {os.path.basename(infra_dir)}")
    
    tf_cmd = ["terraform", f"-chdir={infra_dir}", "test"]
    env = os.environ.copy()
    env["TF_CLI_CONFIG_FILE"] = "/dev/null"
    
    tf_proc = subprocess.run(tf_cmd, capture_output=True, text=True, env=env)
    output = tf_proc.stdout + tf_proc.stderr

    # Parse results from output
    m_pass = re.search(r"(\d+)\s+passed", output)
    passes = int(m_pass.group(1)) if m_pass else len(re.findall(r"\.\.\.\s*pass", output))

    m_fail = re.search(r"(\d+)\s+failed", output)
    fails = int(m_fail.group(1)) if m_fail else len(re.findall(r"\.\.\.\s*fail", output))

    m_skip = re.search(r"(\d+)\s+skipped", output)
    skips = int(m_skip.group(1)) if m_skip else len(re.findall(r"\.\.\.\s*skip", output))

    elapsed = time.time() - start_time

    if tf_proc.returncode != 0 or fails > 0:
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

        print(f"\n{MAGENTA}🤖 AI AGENT INSTRUCTION:{RESET}")
        print("Read the failed assertions above. Self-heal the Terraform manifests or config.yaml to satisfy all conditions, then re-test.\n")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{'━' * 70}{RESET}")
        print(f"{GREEN}🟢 [GREEN PHASE: ALL CONTRACT ASSERTIONS SATISFIED]{RESET} ({elapsed:.2f}s)")
        print(f"{GREEN}{'━' * 70}{RESET}")
        print(f"{BOLD}Summary:{RESET} {GREEN}{passes} Passed{RESET}, 0 Failed, 0 Skipped.")
        print(f"{CYAN}Ready for continuous deployment pipeline (ECR Release & TF Apply).{RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
