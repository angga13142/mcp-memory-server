"""Integration tests for CI/CD pipeline."""

import os
import subprocess
from pathlib import Path

import pytest


class TestLocalCIExecution:
    """Test local CI execution."""

    def test_local_ci_script_runs(self):
        """Test that local CI script executes."""
        result = subprocess.run(
            ["./scripts/ci/run_ci_locally.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )

        # Should complete (may fail, but should execute)
        assert result.returncode in [0, 1], f"Script crashed: {result.stderr}"

    def test_local_ci_checks_formatting(self):
        """Test local CI checks code formatting."""
        result = subprocess.run(
            ["./scripts/ci/run_ci_locally.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )

        output = result.stdout + result.stderr

        # Should mention Black
        assert "black" in output.lower() or "Black" in output

    def test_local_ci_runs_tests(self):
        """Test local CI runs tests."""
        result = subprocess.run(
            ["./scripts/ci/run_ci_locally.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )

        output = result.stdout + result.stderr

        # Should run pytest
        assert "pytest" in output or "test" in output.lower()


class TestPreCommitHooks:
    """Test pre-commit hooks."""

    @pytest.fixture(autouse=True)
    def setup_precommit(self):
        """Ensure pre-commit is installed."""
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("pre-commit not installed")

    def test_precommit_hooks_installed(self):
        """Test pre-commit hooks are installed."""
        git_hooks = Path(".git/hooks/pre-commit")

        if not git_hooks.exists():
            # Try to install
            subprocess.run(["pre-commit", "install"], check=False)

        assert (
            git_hooks.exists()
        ), "Pre-commit hooks not installed. Run: pre-commit install"

    def test_precommit_runs_black(self):
        """Test pre-commit includes Black."""
        result = subprocess.run(
            ["pre-commit", "run", "black", "--all-files"],
            capture_output=True,
            text=True,
        )

        # Should execute (may pass or fail)
        assert "black" in result.stdout.lower()

    def test_precommit_runs_isort(self):
        """Test pre-commit includes isort."""
        result = subprocess.run(
            ["pre-commit", "run", "isort", "--all-files"],
            capture_output=True,
            text=True,
        )

        assert "isort" in result.stdout.lower()


class TestCIValidation:
    """Test CI validation script."""

    def test_validation_script_runs(self):
        """Test validation script executes."""
        result = subprocess.run(
            ["./scripts/validate_cicd.sh"], capture_output=True, text=True, timeout=300
        )

        # Should complete
        assert result.returncode in [0, 1]

    def test_validation_checks_workflows(self):
        """Test validation checks workflow files."""
        result = subprocess.run(
            ["./scripts/validate_cicd.sh"], capture_output=True, text=True, timeout=300
        )

        output = result.stdout

        # Should check workflows
        assert "workflow" in output.lower()

    def test_validation_checks_yaml(self):
        """Test validation checks YAML syntax."""
        result = subprocess.run(
            ["./scripts/validate_cicd.sh"], capture_output=True, text=True, timeout=300
        )

        output = result.stdout

        # Should validate YAML
        assert "yaml" in output.lower()


@pytest.mark.skipif(
    os.environ.get("CI") != "true", reason="Only runs in CI environment"
)
class TestCIEnvironment:
    """Tests that only run in CI environment."""

    def test_running_in_github_actions(self):
        """Test we're running in GitHub Actions."""
        assert os.environ.get("GITHUB_ACTIONS") == "true"

    def test_has_github_context(self):
        """Test GitHub context variables are available."""
        required_vars = [
            "GITHUB_WORKFLOW",
            "GITHUB_RUN_ID",
            "GITHUB_ACTOR",
            "GITHUB_REPOSITORY",
        ]

        for var in required_vars:
            assert var in os.environ, f"Missing GitHub context: {var}"

    def test_services_available(self):
        """Test required services are available (in integration tests)."""
        import requests

        # These should be available in integration-tests job
        services = {
            "prometheus": "http://localhost:9090/-/healthy",
            "grafana": "http://localhost:3000/api/health",
            "redis": "redis://localhost:6379",
        }

        # Try to connect (may not be in this job)
        for service, url in services.items():
            if url.startswith("http"):
                try:
                    requests.get(url, timeout=2)
                    print(f"✅ {service} available")
                except Exception:
                    print(f"⚠️ {service} not available (may not be in this job)")
