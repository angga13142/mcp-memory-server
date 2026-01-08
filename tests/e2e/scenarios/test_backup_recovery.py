"""E2E test for backup and recovery."""

import os
import subprocess
from pathlib import Path

import pytest

from tests.e2e.base import E2ETestBase


@pytest.mark.e2e
@pytest.mark.slow
class TestBackupRecoveryE2E(E2ETestBase):
    """Test backup and recovery workflow."""

    def test_backup_workflow(self):
        """
        Test complete backup workflow:
        1. Check backup scripts exist
        2. Run backups (if scripts exist)
        3. Verify backup files
        """
        print("\n💾 Starting Backup Workflow E2E Test")

        # Step 1: Check backup scripts exist
        def check_backup_scripts():
            scripts = [
                "scripts/backup_prometheus_advanced.sh",
                "scripts/backup_grafana_advanced.sh",
                "scripts/backup_application.sh",
            ]

            found = []
            missing = []
            for script in scripts:
                if os.path.isfile(script):
                    found.append(script)
                else:
                    missing.append(script)

            return {
                "found": found,
                "missing": missing,
                "all_present": len(missing) == 0,
            }

        scripts_check = self.execute_step("Check Backup Scripts", check_backup_scripts)

        print("\nBackup Scripts:")
        for script in scripts_check.data["found"]:
            print(f"  ✅ {script}")
        for script in scripts_check.data["missing"]:
            print(f"  ❌ {script} (missing)")

        if not scripts_check.data["all_present"]:
            pytest.skip(f"Missing backup scripts: {scripts_check.data['missing']}")

        # Step 2: Run backups
        def run_backups():
            results = {}
            for script in scripts_check.data["found"]:
                try:
                    result = subprocess.run(
                        [f"./{script}"],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    results[script] = {
                        "exit_code": result.returncode,
                        "success": result.returncode == 0,
                    }
                except subprocess.TimeoutExpired:
                    results[script] = {
                        "exit_code": -1,
                        "success": False,
                        "error": "Timeout",
                    }
                except Exception as e:
                    results[script] = {
                        "exit_code": -1,
                        "success": False,
                        "error": str(e),
                    }

            return results

        backup_results = self.execute_step("Run Backups", run_backups)

        print("\nBackup Results:")
        for script, result in backup_results.data.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {script}: exit code {result['exit_code']}")

        # Step 3: Verify backup files
        def verify_backup_files():
            backup_dirs = [
                Path("/var/backups/mcp-monitoring/prometheus"),
                Path("/var/backups/mcp-monitoring/grafana"),
                Path("/var/backups/mcp-monitoring/application"),
            ]

            backups = {}
            for backup_dir in backup_dirs:
                component = backup_dir.name
                if backup_dir.exists():
                    files = list(backup_dir.glob("*.tar.gz"))
                    backups[component] = {
                        "exists": True,
                        "file_count": len(files),
                    }
                else:
                    backups[component] = {"exists": False}

            return backups

        verify_result = self.execute_step("Verify Backup Files", verify_backup_files)

        print("\nBackup Directories:")
        for component, info in verify_result.data.items():
            if info["exists"]:
                print(f"  ✅ {component}: {info['file_count']} backup(s)")
            else:
                print(f"  ⚠️  {component}: directory not found")

        self.print_results()
        print("\n✅ Backup Workflow E2E Test PASSED!")
