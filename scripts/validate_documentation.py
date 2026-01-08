#!/usr/bin/env python3
"""
Documentation Validation Script

Validates all monitoring documentation for: 
- Completeness
- Accuracy
- Broken links
- Code examples
- Consistency
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    file: str = ""
    line: int = 0


class DocumentationValidator:
    """Validates documentation files."""

    def __init__(self, docs_dir: Path):
        """
        Initialize validator.

        Args:
            docs_dir: Path to documentation directory
        """
        self.docs_dir = docs_dir
        self.results: List[ValidationResult] = []
        self.stats = {"files_checked": 0, "errors": 0, "warnings": 0, "passed": 0}

    def validate_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all validations passed
        """
        print("🔍 Starting Documentation Validation")
        print("=" * 60)
        print()

        # Run checks
        self._check_file_existence()
        self._check_markdown_syntax()
        self._check_internal_links()
        self._check_code_blocks()
        self._check_headers()
        self._check_consistency()
        self._check_completeness()
        self._validate_commands()
        self._check_table_of_contents()

        # Print results
        self._print_results()

        return self.stats["errors"] == 0

    def _check_file_existence(self):
        """Check all required files exist."""
        print("📄 Checking file existence...")

        required_files = [
            "INDEX.md",
            "README.md",
            "operator-guide.md",
            "developer-guide.md",
            "runbook.md",
            "troubleshooting.md",
            "api-reference.md",
            "architecture.md",
        ]

        for filename in required_files:
            filepath = self.docs_dir / filename

            if filepath.exists():
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"File exists: {filename}",
                        severity="info",
                        file=filename,
                    )
                )
                self.stats["passed"] += 1
            else:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Missing required file: {filename}",
                        severity="error",
                        file=filename,
                    )
                )
                self.stats["errors"] += 1

            self.stats["files_checked"] += 1

    def _check_markdown_syntax(self):
        """Validate Markdown syntax."""
        print("📝 Checking Markdown syntax...")

        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()

            # Check for common Markdown issues
            issues = []

            # Check for unclosed code blocks
            triple_backticks = content.count("```")
            if triple_backticks % 2 != 0:
                issues.append("Unclosed code block (odd number of ```)")

            # Check for broken headers (no space after #)
            broken_headers = re.findall(r"^#{1,6}[^\s#]", content, re.MULTILINE)
            if broken_headers:
                issues.append(f"Broken headers (missing space): {len(broken_headers)}")

            # Check for multiple blank lines
            if "\n\n\n\n" in content:
                issues.append("Multiple consecutive blank lines found")

            if issues:
                for issue in issues:
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Markdown issue in {md_file.name}: {issue}",
                            severity="warning",
                            file=md_file.name,
                        )
                    )
                    self.stats["warnings"] += 1
            else:
                self.results.append(
                    ValidationResult(
                        passed=True,
                        message=f"Markdown syntax valid: {md_file.name}",
                        severity="info",
                        file=md_file.name,
                    )
                )
                self.stats["passed"] += 1

    def _check_internal_links(self):
        """Check internal documentation links."""
        print("🔗 Checking internal links...")

        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()

            # Find all markdown links
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

            for link_text, link_url in links:
                # Skip external links
                if link_url.startswith(("http://", "https://", "mailto:")):
                    continue

                # Parse internal link
                if "#" in link_url:
                    file_part, anchor_part = link_url.split("#", 1)
                else:
                    file_part, anchor_part = link_url, None

                # Check file exists
                if file_part:
                    target_file = self.docs_dir / file_part
                    if not target_file.exists():
                        self.results.append(
                            ValidationResult(
                                passed=False,
                                message=f"Broken link in {md_file.name}: {link_url}",
                                severity="error",
                                file=md_file.name,
                            )
                        )
                        self.stats["errors"] += 1
                        continue
                else:
                    target_file = md_file

                # Check anchor exists
                if anchor_part:
                    target_content = target_file.read_text()

                    # Convert anchor to header format
                    expected_header = anchor_part.replace("-", " ").lower()

                    # Find all headers in target file
                    headers = re.findall(
                        r"^#{1,6}\s+(. +)$", target_content, re.MULTILINE
                    )
                    header_anchors = [
                        h.lower()
                        .replace(" ", "-")
                        .replace(":", "")
                        .replace("&", "")
                        .replace(",", "")
                        for h in headers
                    ]

                    if anchor_part not in header_anchors:
                        self.results.append(
                            ValidationResult(
                                passed=False,
                                message=f"Broken anchor in {md_file.name}:  #{anchor_part}",
                                severity="warning",
                                file=md_file.name,
                            )
                        )
                        self.stats["warnings"] += 1

    def _check_code_blocks(self):
        """Validate code blocks."""
        print("💻 Checking code blocks...")

        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()

            # Find all code blocks
            code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)

            for language, code in code_blocks:
                # Check Python code blocks for syntax
                if language == "python":
                    try:
                        compile(code, "<string>", "exec")
                        self.stats["passed"] += 1
                    except SyntaxError as e:
                        self.results.append(
                            ValidationResult(
                                passed=False,
                                message=f"Python syntax error in {md_file. name}: {e}",
                                severity="error",
                                file=md_file.name,
                                line=e.lineno or 0,
                            )
                        )
                        self.stats["errors"] += 1

                # Check bash code blocks for common issues
                elif language in ("bash", "sh"):
                    # Check for dangerous commands without confirmation
                    dangerous_commands = ["rm -rf /", "dd if=", ":(){ :|:& };:"]
                    for dangerous in dangerous_commands:
                        if dangerous in code:
                            self.results.append(
                                ValidationResult(
                                    passed=False,
                                    message=f"Dangerous command in {md_file.name}: {dangerous}",
                                    severity="warning",
                                    file=md_file.name,
                                )
                            )
                            self.stats["warnings"] += 1

    def _check_headers(self):
        """Check header hierarchy and structure."""
        print("📋 Checking header hierarchy...")

        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()

            # Find all headers
            headers = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)

            prev_level = 0
            for i, (hashes, title) in enumerate(headers):
                level = len(hashes)

                # Check header hierarchy (shouldn't skip levels)
                if prev_level > 0 and level > prev_level + 1:
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Header hierarchy skip in {md_file.name}: {title}",
                            severity="warning",
                            file=md_file.name,
                        )
                    )
                    self.stats["warnings"] += 1

                prev_level = level

    def _check_consistency(self):
        """Check consistency across documents."""
        print("🔄 Checking consistency...")

        # Check for consistent metric naming
        metric_names = set()

        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()

            # Find metric names (mcp_*)
            metrics = re.findall(r"mcp_[a-z_]+", content)
            metric_names.update(metrics)

        # Verify metrics are documented in api-reference.md
        api_ref_file = self.docs_dir / "api-reference.md"
        if api_ref_file.exists():
            api_content = api_ref_file.read_text()

            for metric in metric_names:
                if metric not in api_content:
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Metric {metric} not documented in API reference",
                            severity="warning",
                            file="api-reference.md",
                        )
                    )
                    self.stats["warnings"] += 1

    def _check_completeness(self):
        """Check documentation completeness."""
        print("✅ Checking completeness...")

        required_sections = {
            "README.md": ["Quick Start", "Configuration", "Health Checks"],
            "operator-guide.md": [
                "Installation",
                "Configuration",
                "Operations",
                "Incident Response",
            ],
            "developer-guide.md": [
                "Quick Start",
                "Creating New Metrics",
                "Best Practices",
            ],
            "runbook.md": ["Alert Response", "Service Recovery", "Escalation"],
            "troubleshooting. md": [
                "Quick Diagnostics",
                "Common Issues",
                "Debugging Tools",
            ],
            "api-reference. md": ["Metrics Reference", "HTTP Endpoints", "Alert Rules"],
            "architecture.md": [
                "High-Level Architecture",
                "Component Architecture",
                "Design Decisions",
            ],
        }

        for filename, sections in required_sections.items():
            filepath = self.docs_dir / filename

            if not filepath.exists():
                continue

            content = filepath.read_text()

            for section in sections:
                # Check if section exists (as header)
                if not re.search(
                    rf"^#{1,6}\s+.*{re.escape(section)}",
                    content,
                    re.MULTILINE | re.IGNORECASE,
                ):
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Missing section '{section}' in {filename}",
                            severity="warning",
                            file=filename,
                        )
                    )
                    self.stats["warnings"] += 1

    def _validate_commands(self):
        """Validate shell commands in documentation."""
        print("🔧 Validating commands...")

        # Commands to test (safe ones only)
        safe_commands = {
            "docker-compose ps": "Check if docker-compose is available",
            "curl --version": "Check if curl is available",
            "jq --version": "Check if jq is available",
        }

        for command, description in safe_commands.items():
            try:
                result = subprocess.run(
                    command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )

                if result.returncode == 0:
                    self.results.append(
                        ValidationResult(
                            passed=True,
                            message=f"Command available: {command}",
                            severity="info",
                        )
                    )
                    self.stats["passed"] += 1
                else:
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            message=f"Command failed: {command}",
                            severity="warning",
                        )
                    )
                    self.stats["warnings"] += 1

            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"Command not found: {command}",
                        severity="info",
                    )
                )

    def _check_table_of_contents(self):
        """Check if INDEX.md table of contents is accurate."""
        print("📑 Checking table of contents...")

        index_file = self.docs_dir / "INDEX.md"
        if not index_file.exists():
            return

        index_content = index_file.read_text()

        # Check all files mentioned in INDEX exist
        referenced_files = re.findall(
            r"\[([^\]]+)\]\(([^)]+\.md)[^)]*\)", index_content
        )

        for link_text, filename in referenced_files:
            filepath = self.docs_dir / filename

            if not filepath.exists():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        message=f"INDEX.md references missing file: {filename}",
                        severity="error",
                        file="INDEX.md",
                    )
                )
                self.stats["errors"] += 1

    def _print_results(self):
        """Print validation results."""
        print()
        print("=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)
        print()

        # Group results by severity
        errors = [r for r in self.results if r.severity == "error" and not r.passed]
        warnings = [r for r in self.results if r.severity == "warning" and not r.passed]

        # Print errors
        if errors:
            print("❌ ERRORS:")
            for result in errors:
                print(f"   [{result.file}] {result.message}")
            print()

        # Print warnings
        if warnings:
            print("⚠️  WARNINGS:")
            for result in warnings[:10]:  # Show first 10
                print(f"   [{result.file}] {result.message}")

            if len(warnings) > 10:
                print(f"   ... and {len(warnings) - 10} more warnings")
            print()

        # Print statistics
        print("📈 STATISTICS:")
        print(f"   Files checked: {self.stats['files_checked']}")
        print(f"   Passed checks: {self.stats['passed']}")
        print(f"   Errors: {self.stats['errors']}")
        print(f"   Warnings: {self. stats['warnings']}")
        print()

        # Overall status
        if self.stats["errors"] == 0:
            if self.stats["warnings"] == 0:
                print("✅ ALL VALIDATIONS PASSED!")
            else:
                print("✅ PASSED (with warnings)")
        else:
            print("❌ VALIDATION FAILED")

        print()


def main():
    """Main entry point."""
    # Find docs directory
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent / "docs" / "monitoring"

    if not docs_dir.exists():
        print(f"❌ Documentation directory not found: {docs_dir}")
        sys.exit(1)

    # Run validation
    validator = DocumentationValidator(docs_dir)
    success = validator.validate_all()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
