"""Regression tests for the orchestrator's verification verdicts."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tdd_orchestrator as orchestrator


class VerificationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.infra = self.root / "module"
        self.deploy = self.root / "deploy"
        for path in (self.infra, self.deploy):
            path.mkdir()
            (path / "main.tf").touch()
        self.config = self.deploy / "config.yaml"
        self.config.write_text("NAME: example\nPORT: 8080\n", encoding="utf-8")
        self.contract = self.infra / "app_contract.tftest.hcl"
        self.contract.touch()
        self.checker = self.root / "tests/check_ingress_collisions.py"
        self.checker.parent.mkdir()
        self.checker.touch()

    def run_orchestrator(self, *flags, ingress_result=(0, "", None)):
        args = ["tdd_orchestrator.py", "--config", str(self.config), "--infra-dir", str(self.infra), *flags]

        def tool_result(command, **kwargs):
            if str(self.checker) in command:
                return ingress_result
            if "test" in command:
                return 0, "Success! 1 passed, 0 failed.", None
            return 0, "", None

        output = io.StringIO()
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(sys, "argv", args),
            patch.object(orchestrator, "PLUGIN_ROOT", self.root),
            patch.object(orchestrator, "run_tool", side_effect=tool_result) as runner,
            redirect_stdout(output),
            redirect_stderr(output),
            self.assertRaises(SystemExit) as exit_result,
        ):
            orchestrator.main()
        commands = [call.args[0] for call in runner.call_args_list]
        return exit_result.exception.code, output.getvalue(), commands

    def test_missing_ingress_checker_prevents_green(self):
        self.checker.unlink()
        code, output, _ = self.run_orchestrator()
        self.assertEqual(code, 0, output)
        self.assertIn("PARTIAL", output)
        self.assertNotIn("GREEN PHASE", output)

    def test_strict_mode_rejects_incomplete_ingress_verification(self):
        code, output, _ = self.run_orchestrator("--strict", ingress_result=(3, "No peers available", None))
        self.assertEqual(code, 3, output)
        self.assertIn("PARTIAL", output)
        self.assertNotIn("GREEN PHASE", output)

    def test_unrelated_smoke_test_cannot_replace_app_contract(self):
        self.contract.rename(self.infra / "smoke.tftest.hcl")
        code, output, commands = self.run_orchestrator()
        self.assertEqual(code, 1, output)
        self.assertIn("CONTRACT_TEST_NOT_FOUND", output)
        self.assertFalse(any("test" in command for command in commands))

    def test_green_run_filters_terraform_to_the_selected_contract(self):
        code, output, commands = self.run_orchestrator("--strict")
        self.assertEqual(code, 0, output)
        self.assertIn("GREEN PHASE", output)
        test_command = next(command for command in commands if "test" in command)
        self.assertIn("-filter=app_contract.tftest.hcl", test_command)


if __name__ == "__main__":
    unittest.main()
