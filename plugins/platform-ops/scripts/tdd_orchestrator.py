#!/usr/bin/env python3
"""
TDD IaC Orchestrator & Live Demo Test Runner
Executes the Red-Green-Refactor loop:
  1. Validates declarative config against JSON Schema
  2. Runs native Terraform contract tests (*.tftest.hcl) in mock mode
  3. Formats presentation-friendly RED / GREEN output for human audience & AI self-healing
"""

import sys
import os
import subprocess
import time
import re

# Auto-elevate to workspace venv python if available
for _sub in ["ZIPPO-INFR/.venv/bin/python3", ".venv/bin/python3"]:
    _cand = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", _sub))
    if os.path.exists(_cand) and sys.executable != _cand:
        os.execv(_cand, [_cand] + sys.argv)


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

def main():
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Search for aws-epam-ecs-app or fallback to plugin tests
    test_module_dir = None
    search_dirs = [
        os.path.abspath(os.path.join(plugin_dir, "../../../ZIPPO-INFR/iac/aws-epam-ecs-app")),
        os.path.abspath(os.path.join(plugin_dir, "../../ZIPPO-INFR/iac/aws-epam-ecs-app")),
        os.path.abspath(os.path.join(plugin_dir, "tests/tftests"))
    ]
    for d in search_dirs:
        if os.path.exists(d):
            test_module_dir = d
            break
            
    validator_script = os.path.join(plugin_dir, "tests/validate_configs.py")


    target_config = sys.argv[1] if len(sys.argv) > 1 else None

    print_banner("AI-DRIVEN IAC ORCHESTRATOR: TDD LOOP")
    start_time = time.time()

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: Schema Contract Validation (SDD)
    # ─────────────────────────────────────────────────────────────
    if target_config and os.path.exists(target_config):
        run_step(f"Validating Specification ({os.path.basename(target_config)})")
        val_cmd = [sys.executable, validator_script, target_config]
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
    run_step("Executing Native Terraform Contract Tests (*.tftest.hcl)")
    
    tf_cmd = ["terraform", f"-chdir={test_module_dir}", "test"]
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
            if "fail" in line or "Error:" in line or "error_message" in line or "Error while" in line:
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
