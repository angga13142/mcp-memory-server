"""Configuration for CI tests."""

import pytest


@pytest.fixture
def mock_github_env(monkeypatch):
    """Mock GitHub Actions environment variables."""
    github_env = {
        "CI": "true",
        "GITHUB_ACTIONS": "true",
        "GITHUB_WORKFLOW": "Test Workflow",
        "GITHUB_RUN_ID": "123456",
        "GITHUB_RUN_NUMBER": "42",
        "GITHUB_ACTOR": "test-user",
        "GITHUB_REPOSITORY": "test-org/test-repo",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_SHA": "abc123def456",
        "GITHUB_EVENT_NAME": "push",
    }

    for key, value in github_env.items():
        monkeypatch.setenv(key, value)

    return github_env


@pytest.fixture
def temp_workflow_file(tmp_path):
    """Create a temporary workflow file for testing."""
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)

    workflow_file = workflow_dir / "test.yml"
    workflow_content = """
name: Test Workflow

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: echo "Testing"
"""
    workflow_file.write_text(workflow_content)

    return workflow_file
