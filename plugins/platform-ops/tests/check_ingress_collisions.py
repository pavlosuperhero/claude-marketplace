#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Cross-Service ALB Ingress Collision Detector

The app-config schema documents that `ALB.priority` "must be unique across services
sharing the ALB", but a single-file schema check cannot enforce a cross-file invariant.
This script closes that gap: it reads every sibling service config for the same
environment and reports routing conflicts deterministically.

It NEVER resolves a conflict. Reassigning a path pattern or priority decides which
service receives production traffic — and, for a catch-all, which service goes dark.
That is a human decision. This script escalates with enumerated options and exits 2.

Exit codes (stable contract for the orchestrator and for LLM agents):
  0 - no collision detected
  1 - script could not run (bad args, unreadable config, unparseable YAML)
  2 - COLLISION DETECTED, escalation required, do not auto-resolve

CLI Usage:
  uv run tests/check_ingress_collisions.py --config /path/to/deploy/dev/config.yaml
  uv run tests/check_ingress_collisions.py --config <path> --workspace-root /path/to/workspace
"""

import sys
import os
import glob
import argparse

import yaml

SEP = "=" * 70


def load_config(path):
    """Return (config_dict, error_string). Never raises."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except PermissionError as e:
        return None, f"permission denied reading {path}: {e}"
    except yaml.YAMLError as e:
        return None, f"invalid YAML in {path}: {e}"
    except OSError as e:
        return None, f"could not read {path}: {e}"

    if data is None:
        return None, f"empty YAML document: {path}"
    if not isinstance(data, dict):
        return None, f"expected a YAML mapping at top level, got {type(data).__name__}: {path}"
    return data, None


def describe(path, config, fallback_name):
    """Flatten one config into the ingress facts we compare across services."""
    alb = config.get("ALB") or {}
    if not isinstance(alb, dict):
        alb = {}
    patterns = alb.get("path_patterns") or []
    if not isinstance(patterns, list):
        patterns = [patterns]
    return {
        "service": config.get("NAME") or fallback_name,
        "repo": fallback_name,
        "path": path,
        "priority": alb.get("priority"),
        "patterns": [str(p) for p in patterns],
        "has_alb": bool(alb),
    }


def is_catch_all(pattern):
    return pattern.strip() in ("/*", "/**", "*")


def find_peers(config_path, workspace_root=None):
    """
    Discover sibling service configs for the same environment.

    A config at <workspace>/<REPO>/deploy/<env>/config.yaml has peers at
    <workspace>/*/deploy/<env>/config.yaml. Returns (peer_paths, env, workspace_root).
    """
    deploy_env_dir = os.path.dirname(os.path.abspath(config_path))
    env = os.path.basename(deploy_env_dir)
    repo_dir = os.path.dirname(os.path.dirname(deploy_env_dir))

    root = os.path.abspath(workspace_root) if workspace_root else os.path.dirname(repo_dir)
    pattern = os.path.join(root, "*", "deploy", env, "config.yaml")
    peers = sorted(p for p in glob.glob(pattern) if os.path.abspath(p) != os.path.abspath(config_path))
    return peers, env, root


def detect(subject, peers):
    """
    Compare the subject against each peer. Returns a list of conflict dicts.
    Pure function over already-loaded facts — no I/O, so the result is reproducible.
    """
    conflicts = []
    for peer in peers:
        if not peer["has_alb"]:
            continue

        if subject["priority"] is not None and subject["priority"] == peer["priority"]:
            conflicts.append({
                "kind": "DUPLICATE_PRIORITY",
                "severity": "HARD",
                "peer": peer,
                "detail": (
                    f"both services declare ALB.priority {subject['priority']} on the shared "
                    f"listener; AWS rejects the second apply with PriorityInUse"
                ),
            })

        shared = [p for p in subject["patterns"] if p in peer["patterns"]]
        if shared:
            conflicts.append({
                "kind": "DUPLICATE_PATH_PATTERN",
                "severity": "HARD",
                "peer": peer,
                "detail": (
                    f"both services claim path pattern(s) {shared}; only the lower priority "
                    f"number ever matches, so the other target group receives no traffic"
                ),
            })

        # A catch-all at a lower priority number shadows everything numerically after it.
        for pattern in peer["patterns"]:
            if (
                is_catch_all(pattern)
                and peer["priority"] is not None
                and subject["priority"] is not None
                and peer["priority"] < subject["priority"]
                and not shared
            ):
                conflicts.append({
                    "kind": "SHADOWED_BY_CATCH_ALL",
                    "severity": "HARD",
                    "peer": peer,
                    "detail": (
                        f"peer owns catch-all '{pattern}' at priority {peer['priority']}, which is "
                        f"evaluated before this service's priority {subject['priority']}; "
                        f"this service is unreachable"
                    ),
                })
    return conflicts


def suggest_priority(peers):
    """Lowest free priority in steps of 10 that lands before every peer catch-all."""
    taken = {p["priority"] for p in peers if p["priority"] is not None}
    taken.discard(None)
    ceiling = min(
        [p["priority"] for p in peers
         if p["priority"] is not None and any(is_catch_all(x) for x in p["patterns"])],
        default=50000,
    )
    for candidate in range(10, max(ceiling, 11), 10):
        if candidate not in taken:
            return candidate
    for candidate in range(1, max(ceiling, 2)):
        if candidate not in taken:
            return candidate
    return None


def suggest_path(subject):
    name = str(subject["service"]).strip().lower().replace("_", "-")
    return f"/{name}/*" if name else "/<service>/*"


def report(subject, conflicts, peers, env):
    print(SEP)
    print("ALB INGRESS COLLISION DETECTED - ESCALATION REQUIRED")
    print(SEP)
    print(f"Environment:      {env}")
    print(f"Subject service:  {subject['service']}  ({subject['path']})")
    print(f"  priority:       {subject['priority']}")
    print(f"  path_patterns:  {subject['patterns']}")
    print()

    for i, c in enumerate(conflicts, 1):
        peer = c["peer"]
        print(f"[{i}] {c['severity']} - {c['kind']}")
        print(f"    conflicts with: {peer['service']}  ({peer['path']})")
        print(f"      priority:      {peer['priority']}")
        print(f"      path_patterns: {peer['patterns']}")
        print(f"    consequence:    {c['detail']}")
        print()

    print(SEP)
    print("CURRENT INGRESS MAP FOR THIS ENVIRONMENT")
    print(SEP)
    rows = [subject] + [p for p in peers if p["has_alb"]]
    for r in sorted(rows, key=lambda x: (x["priority"] is None, x["priority"])):
        marker = " <- subject" if r["path"] == subject["path"] else ""
        print(f"  priority {str(r['priority']):>6}  {str(r['patterns']):<24} {r['service']}{marker}")
    print()

    alt_priority = suggest_priority(peers)
    alt_path = suggest_path(subject)
    displaced = sorted({c["peer"]["service"] for c in conflicts})

    print(SEP)
    print("OPTIONS - REQUIRES HUMAN DECISION, DO NOT SELECT ONE AUTONOMOUSLY")
    print(SEP)
    print(f"  A) COEXIST - move '{subject['service']}' to its own route.")
    print(f"     Set path_patterns: [\"{alt_path}\"] and priority: {alt_priority}.")
    print(f"     Both services stay live. {', '.join(displaced)} keeps its current route.")
    print(f"     The exact prefix is a product decision - '{alt_path}' is a placeholder.")
    print()
    print(f"  B) REPLACE - '{subject['service']}' takes over the route.")
    print(f"     This DECOMMISSIONS {', '.join(displaced)}: its listener rule and target")
    print(f"     group must be explicitly removed. Existing URLs served by it will break.")
    print(f"     Treat as a separate, reviewed change - never a side effect of onboarding.")
    print()
    print(f"  C) COEXIST, INVERTED - {', '.join(displaced)} moves instead.")
    print(f"     '{subject['service']}' keeps its declared route; the peer takes a specific")
    print(f"     prefix. Both stay live, but URLs currently served by the peer will break.")
    print()
    print(f"  D) DEFER - leave every config unchanged and resolve routing separately.")
    print()
    print(SEP)
    print("AI AGENT INSTRUCTION")
    print(SEP)
    print("STOP. Do not edit any config.yaml to resolve this.")
    print("Report the conflict above to the human, present options A-D verbatim, and ask")
    print("which they want. Reassigning a catch-all decides which service receives")
    print("production traffic and which goes dark; that authority is not yours.")
    print("Resume only after the human states a choice explicitly.")
    print(SEP)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect ALB listener rule collisions across sibling service configs."
    )
    parser.add_argument(
        "-c", "--config",
        dest="config_path",
        default=os.environ.get("APP_CONFIG_PATH"),
        help="Path to the service deploy config.yaml to check (or env APP_CONFIG_PATH).",
    )
    parser.add_argument(
        "-w", "--workspace-root",
        dest="workspace_root",
        default=os.environ.get("WORKSPACE_ROOT"),
        help="Directory containing all service repos. Defaults to the subject repo's parent.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.config_path:
        print("Error: no config specified. Pass --config or set APP_CONFIG_PATH.", file=sys.stderr)
        sys.exit(1)

    config_path = os.path.abspath(args.config_path)
    config, err = load_config(config_path)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    repo_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(config_path))))
    subject = describe(config_path, config, repo_name)

    print(SEP)
    print("CROSS-SERVICE ALB INGRESS CHECK")
    print(SEP)

    if not subject["has_alb"]:
        print(f"Subject '{subject['service']}' declares no ALB block - no ingress to compare.")
        sys.exit(0)

    peer_paths, env, root = find_peers(config_path, args.workspace_root)
    print(f"Environment:    {env}")
    print(f"Workspace root: {root}")
    print(f"Peer configs:   {len(peer_paths)} discovered")

    peers, unreadable = [], []
    for p in peer_paths:
        peer_config, peer_err = load_config(p)
        if peer_err:
            unreadable.append(peer_err)
            continue
        peers.append(describe(p, peer_config, os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))))

    for u in unreadable:
        # Surfaced, never swallowed: an unread peer is an ungated collision risk.
        print(f"  WARNING: skipped unreadable peer - {u}")
    if not peer_paths:
        print("  Note: no sibling configs found. If peers exist elsewhere, pass --workspace-root;")
        print("        an empty peer set means this check proved nothing.")
    print()

    conflicts = detect(subject, peers)
    if not conflicts:
        print(f"OK: no ingress collision between '{subject['service']}' and {len(peers)} peer(s).")
        for r in sorted([subject] + [p for p in peers if p["has_alb"]],
                        key=lambda x: (x["priority"] is None, x["priority"])):
            print(f"  priority {str(r['priority']):>6}  {str(r['patterns']):<24} {r['service']}")
        sys.exit(0)

    report(subject, conflicts, peers, env)
    sys.exit(2)


if __name__ == "__main__":
    main()
