"""Tests for CI/CD workflow configuration."""

from pathlib import Path
from typing import Any

import pytest
import yaml


def get_triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    """Get triggers from workflow, handling PyYAML 'on' -> True conversion."""
    if "on" in workflow:
        return workflow["on"]
    if True in workflow:
        return workflow[True]
    return {}


class TestWorkflowConfiguration:
    """Test CI/CD workflow configurations."""

    @pytest.fixture
    def workflows_dir(self):
        """Get workflows directory."""
        return Path(".github/workflows")

    @pytest.fixture
    def workflow_files(self, workflows_dir):
        """Get all workflow files."""
        return list(workflows_dir.glob("*.yml"))

    def test_workflow_files_exist(self, workflows_dir):
        """Test that required workflow files exist."""
        required_workflows = [
            "monitoring-ci.yml",
            "pr-validation.yml",
            "nightly-build.yml",
        ]

        for workflow in required_workflows:
            workflow_path = workflows_dir / workflow
            assert workflow_path.exists(), f"Missing workflow: {workflow}"

    def test_workflow_yaml_valid(self, workflow_files):
        """Test that all workflow files have valid YAML syntax."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")

    def test_workflow_has_name(self, workflow_files):
        """Test that all workflows have a name."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)
                assert (
                    "name" in workflow
                ), f"Workflow {workflow_file.name} missing 'name'"
                assert workflow[
                    "name"
                ], f"Workflow {workflow_file.name} has empty 'name'"

    def test_workflow_has_triggers(self, workflow_files):
        """Test that all workflows have proper triggers."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)
                triggers = get_triggers(workflow)
                assert (
                    triggers
                ), f"Workflow {workflow_file.name} has no triggers defined (checked 'on' and True)"

    def test_workflow_has_jobs(self, workflow_files):
        """Test that all workflows have jobs defined."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)
                assert (
                    "jobs" in workflow
                ), f"Workflow {workflow_file.name} missing 'jobs'"
                assert workflow[
                    "jobs"
                ], f"Workflow {workflow_file.name} has no jobs defined"

    def test_jobs_have_required_fields(self, workflow_files):
        """Test that jobs have required fields."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)

                for job_name, job_config in workflow.get("jobs", {}).items():
                    # Check runs-on
                    assert (
                        "runs-on" in job_config
                    ), f"Job '{job_name}' in {workflow_file.name} missing 'runs-on'"

                    # Check steps (unless it's a reusable workflow)
                    if "uses" not in job_config:
                        assert (
                            "steps" in job_config
                        ), f"Job '{job_name}' in {workflow_file.name} missing 'steps'"

    def test_steps_have_names(self, workflow_files):
        """Test that all steps have names for clarity."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)

                for job_name, job_config in workflow.get("jobs", {}).items():
                    steps = job_config.get("steps", [])

                    for i, step in enumerate(steps):
                        if "name" not in step:
                            # Allow unnamed steps for actions like checkout
                            if "uses" in step and "actions/checkout" in step["uses"]:
                                continue

                            pytest.fail(
                                f"Step {i} in job '{job_name}' ({workflow_file.name}) "
                                f"missing 'name'"
                            )

    def test_python_version_consistency(self, workflow_files):
        """Test that Python version is consistent across workflows."""
        python_versions = set()

        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                content = f.read()
                workflow = yaml.safe_load(content)

                # Check env variables
                if "env" in workflow and "PYTHON_VERSION" in workflow["env"]:
                    python_versions.add(workflow["env"]["PYTHON_VERSION"])

                # Check in jobs
                for job_config in workflow.get("jobs", {}).values():
                    for step in job_config.get("steps", []):
                        if (
                            step.get("uses", "").startswith("actions/setup-python")
                            and "with" in step
                            and "python-version" in step["with"]
                        ):
                            version = step["with"]["python-version"]
                            # Handle variable references
                            if not version.startswith("${{"):
                                python_versions.add(version)

        # Should have consistent version (or use variables)
        assert (
            len(python_versions) <= 1
        ), f"Inconsistent Python versions: {python_versions}"


class TestMonitoringCIWorkflow:
    """Test main monitoring CI/CD workflow."""

    @pytest.fixture
    def workflow(self):
        """Load monitoring CI workflow."""
        with open(".github/workflows/monitoring-ci.yml") as f:
            return yaml.safe_load(f)

    def test_triggers_on_push(self, workflow):
        """Test workflow triggers on push to main/develop."""
        triggers = get_triggers(workflow)

        assert "push" in triggers
        assert "branches" in triggers["push"]

        branches = triggers["push"]["branches"]
        assert "main" in branches
        assert "develop" in branches

    def test_triggers_on_pr(self, workflow):
        """Test workflow triggers on pull requests."""
        triggers = get_triggers(workflow)

        assert "pull_request" in triggers
        assert "branches" in triggers["pull_request"]

    def test_has_path_filters(self, workflow):
        """Test workflow has path filters for efficiency."""
        triggers = get_triggers(workflow)

        # Should have paths for push/PR to avoid unnecessary runs
        if "push" in triggers:
            assert "paths" in triggers["push"]

        if "pull_request" in triggers:
            assert "paths" in triggers["pull_request"]

    def test_has_required_jobs(self, workflow):
        """Test workflow has all required jobs."""
        required_jobs = [
            "code-quality",
            "unit-tests",
            "integration-tests",
            "docs-validation",
            "docker-build",
        ]

        jobs = workflow["jobs"]

        for required_job in required_jobs:
            assert required_job in jobs, f"Missing required job: {required_job}"

    def test_unit_tests_job_configuration(self, workflow):
        """Test unit tests job is properly configured."""
        unit_tests = workflow["jobs"]["unit-tests"]

        # Check runs-on
        assert unit_tests["runs-on"] == "ubuntu-latest"

        # Check steps include pytest
        steps = unit_tests["steps"]
        step_commands = [step.get("run", "") for step in steps]

        pytest_found = any("pytest" in cmd for cmd in step_commands)
        assert pytest_found, "Unit tests job doesn't run pytest"

        # Check coverage
        coverage_found = any("--cov" in cmd for cmd in step_commands)
        assert coverage_found, "Unit tests don't measure coverage"

    def test_integration_tests_have_services(self, workflow):
        """Test integration tests job has required services."""
        integration_tests = workflow["jobs"]["integration-tests"]

        assert "services" in integration_tests, "Integration tests missing services"

        services = integration_tests["services"]

        # Check required services
        assert "prometheus" in services
        assert "grafana" in services
        assert "redis" in services

    def test_services_have_health_checks(self, workflow):
        """Test services have health checks configured."""
        integration_tests = workflow["jobs"]["integration-tests"]
        services = integration_tests["services"]

        for service_name, service_config in services.items():
            assert (
                "options" in service_config
            ), f"Service {service_name} missing health check options"

            options = service_config["options"]
            assert (
                "--health-cmd" in options
            ), f"Service {service_name} missing health-cmd"

    def test_load_tests_conditional(self, workflow):
        """Test load tests only run on push, not PR."""
        load_tests = workflow["jobs"].get("load-tests")

        if load_tests:
            assert "if" in load_tests, "Load tests should be conditional"

            condition = load_tests["if"]
            # Should not run on PR
            assert "pull_request" not in condition or "push" in condition

    def test_deployment_jobs_protected(self, workflow):
        """Test deployment jobs have proper conditions."""
        deploy_jobs = ["deploy-staging", "deploy-production"]

        for job_name in deploy_jobs:
            if job_name in workflow["jobs"]:
                job = workflow["jobs"][job_name]

                # Should have branch condition
                assert (
                    "if" in job
                ), f"Deployment job {job_name} not protected by condition"

                # Should have environment
                assert (
                    "environment" in job
                ), f"Deployment job {job_name} missing environment"

    def test_artifact_uploads(self, workflow):
        """Test that jobs upload artifacts."""
        jobs = workflow["jobs"]

        jobs_with_artifacts = ["code-quality", "unit-tests", "integration-tests"]

        for job_name in jobs_with_artifacts:
            job = jobs[job_name]
            steps = job["steps"]

            # Find upload-artifact steps
            upload_steps = [
                step
                for step in steps
                if step.get("uses", "").startswith("actions/upload-artifact")
            ]

            assert len(upload_steps) > 0, f"Job {job_name} doesn't upload any artifacts"


class TestPRValidationWorkflow:
    """Test PR validation workflow."""

    @pytest.fixture
    def workflow(self):
        """Load PR validation workflow."""
        with open(".github/workflows/pr-validation.yml") as f:
            return yaml.safe_load(f)

    def test_only_triggers_on_pr(self, workflow):
        """Test workflow only triggers on pull requests."""
        triggers = get_triggers(workflow)

        assert "pull_request" in triggers

        # Should specify PR types
        assert "types" in triggers["pull_request"]

        pr_types = triggers["pull_request"]["types"]
        assert "opened" in pr_types
        assert "synchronize" in pr_types

    def test_has_pr_checks(self, workflow):
        """Test workflow has PR-specific checks."""
        jobs = workflow["jobs"]

        assert "pr-checks" in jobs

    def test_checks_pr_title(self, workflow):
        """Test workflow validates PR title format."""
        pr_checks = workflow["jobs"]["pr-checks"]
        steps = pr_checks["steps"]

        # Find PR title check step
        title_check = None
        for step in steps:
            if "Check PR title" in step.get("name", ""):
                title_check = step
                break

        assert title_check is not None, "No PR title check found"
        assert "run" in title_check


class TestNightlyBuildWorkflow:
    """Test nightly build workflow."""

    @pytest.fixture
    def workflow(self):
        """Load nightly build workflow."""
        with open(".github/workflows/nightly-build.yml") as f:
            return yaml.safe_load(f)

    def test_has_schedule_trigger(self, workflow):
        """Test workflow has schedule trigger."""
        triggers = get_triggers(workflow)

        assert "schedule" in triggers

        schedule = triggers["schedule"]
        assert len(schedule) > 0

        # Should have cron expression
        assert "cron" in schedule[0]

    def test_has_manual_trigger(self, workflow):
        """Test workflow can be triggered manually."""
        triggers = get_triggers(workflow)

        assert "workflow_dispatch" in triggers

    def test_runs_extended_tests(self, workflow):
        """Test nightly build runs extended tests."""
        jobs = workflow["jobs"]

        assert "extended-tests" in jobs or any(
            "extended" in job_name.lower() for job_name in jobs
        )


class TestConfigurationFiles:
    """Test CI/CD configuration files."""

    def test_markdownlint_config_exists(self):
        """Test markdownlint configuration exists."""
        config_path = Path(".markdownlint.json")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "default" in config

    def test_codecov_config_exists(self):
        """Test codecov configuration exists."""
        config_path = Path(".codecov.yml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "coverage" in config

    def test_codecov_threshold_configured(self):
        """Test codecov has proper threshold."""
        with open(".codecov.yml") as f:
            config = yaml.safe_load(f)

            coverage = config["coverage"]
            assert "status" in coverage

            project = coverage["status"]["project"]
            assert "default" in project

            target = project["default"]["target"]
            # Should be 85% or similar
            assert target.endswith("%")
            threshold = int(target.rstrip("%"))
            assert threshold >= 80

    def test_precommit_config_exists(self):
        """Test pre-commit configuration exists."""
        config_path = Path(".pre-commit-config.yaml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "repos" in config

    def test_precommit_has_required_hooks(self):
        """Test pre-commit has required hooks."""
        with open(".pre-commit-config.yaml") as f:
            config = yaml.safe_load(f)

            repos = config["repos"]

            # Collect all hook IDs
            hook_ids = []
            for repo in repos:
                for hook in repo.get("hooks", []):
                    hook_ids.append(hook["id"])

            required_hooks = ["black", "isort", "ruff"]

            for required in required_hooks:
                assert (
                    required in hook_ids
                ), f"Missing required pre-commit hook: {required}"

    def test_dependabot_config_exists(self):
        """Test dependabot configuration exists."""
        config_path = Path(".github/dependabot.yml")
        assert config_path.exists()

        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "version" in config
            assert config["version"] == 2
            assert "updates" in config

    def test_dependabot_monitors_python(self):
        """Test dependabot monitors Python dependencies."""
        with open(".github/dependabot.yml") as f:
            config = yaml.safe_load(f)

            updates = config["updates"]

            ecosystems = [update["package-ecosystem"] for update in updates]
            assert "pip" in ecosystems


class TestCIScripts:
    """Test CI-related scripts."""

    def test_local_ci_script_exists(self):
        """Test local CI runner script exists."""
        script_path = Path("scripts/run_ci_locally.sh")
        assert script_path.exists()

    def test_local_ci_script_executable(self):
        """Test local CI script is executable."""
        script_path = Path("scripts/run_ci_locally.sh")
        assert script_path.stat().st_mode & 0o111, "run_ci_locally.sh is not executable"

    def test_local_ci_script_has_checks(self):
        """Test local CI script includes required checks."""
        with open("scripts/run_ci_locally.sh") as f:
            content = f.read()

            required_checks = ["black", "isort", "ruff", "pytest", "bandit"]

            for check in required_checks:
                assert check in content, f"Local CI script missing {check} check"

    def test_validation_script_exists(self):
        """Test CI/CD validation script exists."""
        script_path = Path("scripts/validate_cicd.sh")
        assert script_path.exists()

    def test_validation_script_executable(self):
        """Test validation script is executable."""
        script_path = Path("scripts/validate_cicd.sh")
        assert script_path.stat().st_mode & 0o111


class TestWorkflowSecurity:
    """Test security aspects of workflows."""

    @pytest.fixture
    def workflow_files(self):
        """Get all workflow files."""
        return list(Path(".github/workflows").glob("*.yml"))

    def test_no_hardcoded_secrets(self, workflow_files):
        """Test workflows don't have hardcoded secrets."""
        sensitive_patterns = ["password: ", "api_key:", "secret:", "token:"]

        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                content = f.read().lower()

                for pattern in sensitive_patterns:
                    start = 0
                    while True:
                        try:
                            idx = content.index(pattern, start)
                        except ValueError:
                            break

                        # Look at context around the match (before and after)
                        context_start = max(0, idx - 50)
                        context_end = min(len(content), idx + 100)
                        context = content[context_start:context_end]

                        # Check if this specific instance is allowed
                        if (
                            "gf_security_admin_password: admin" in context
                            or "grafana_password: admin" in context
                        ):
                            start = idx + 1
                            continue

                        assert (
                            "secrets." in context or "${{" in context
                        ), f"Potential hardcoded secret in {workflow_file.name} at index {idx}: {context}"

                        start = idx + 1

    def test_secrets_use_proper_syntax(self, workflow_files):
        """Test secrets use proper GitHub syntax."""
        import re

        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                content = f.read()

                # Find secret references
                secret_refs = re.findall(r"secrets\.\w+", content)

                for ref in secret_refs:
                    # Should be uppercase
                    secret_name = ref.split(".")[1]
                    assert secret_name.isupper() or secret_name.startswith(
                        "GITHUB_"
                    ), f"Secret {ref} in {workflow_file.name} should be uppercase"

    def test_workflow_permissions_defined(self, workflow_files):
        """Test workflows have permissions defined (best practice)."""
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)

                # Check top-level or job-level permissions
                has_permissions = "permissions" in workflow

                if not has_permissions:
                    # Check job-level permissions
                    for job in workflow.get("jobs", {}).values():
                        if "permissions" in job:
                            has_permissions = True
                            break

                # Warning, not failure (optional best practice)
                if not has_permissions:
                    print(f"Warning: {workflow_file.name} has no explicit permissions")


class TestWorkflowEfficiency:
    """Test workflow efficiency and optimization."""

    @pytest.fixture
    def monitoring_ci(self):
        """Load main CI workflow."""
        with open(".github/workflows/monitoring-ci.yml") as f:
            return yaml.safe_load(f)

    def test_uses_caching(self, monitoring_ci):
        """Test workflows use caching for dependencies."""
        jobs = monitoring_ci["jobs"]

        # Check if any job uses caching
        uses_cache = False

        for job in jobs.values():
            for step in job.get("steps", []):
                if (
                    step.get("uses", "").startswith("actions/setup-python")
                    and "with" in step
                    and "cache" in step["with"]
                ):
                    uses_cache = True
                    break

        assert uses_cache, "No jobs use Python dependency caching"

    def test_jobs_run_in_parallel(self, monitoring_ci):
        """Test independent jobs can run in parallel."""
        jobs = monitoring_ci["jobs"]

        # Count jobs with 'needs' dependency
        jobs_with_deps = sum(1 for job in jobs.values() if "needs" in job)

        # Should have some parallel jobs (no needs)
        parallel_jobs = len(jobs) - jobs_with_deps
        assert parallel_jobs > 0, "All jobs are sequential (no parallelism)"

    def test_checkout_uses_latest(self, monitoring_ci):
        """Test checkout action uses recommended version."""
        jobs = monitoring_ci["jobs"]

        for job in jobs.values():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/checkout"):
                    version = step["uses"].split("@")[1]
                    # Should use v3 or v4
                    assert version in [
                        "v3",
                        "v4",
                    ], f"Checkout action using old version: {version}"
