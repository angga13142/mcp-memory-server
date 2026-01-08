# VALIDATION PROMPT 5.3: CI/CD Pipeline Validation

## 🎯 Objective
Validate that CI/CD pipeline is properly configured and all workflows execute correctly in GitHub Actions.

## ✅ Pre-Validation Checklist

### Code Review
- [ ] `.github/workflows/monitoring-ci.yml` exists
- [ ] `.github/workflows/pr-validation.yml` exists
- [ ] `.github/workflows/nightly-build.yml` exists
- [ ] `.github/dependabot.yml` exists
- [ ] `.markdownlint.json` exists
- [ ] `.codecov.yml` exists
- [ ] `.pre-commit-config.yaml` exists
- [ ] `scripts/run_ci_locally.sh` exists and is executable

### Repository Setup
```bash
# Check if running on GitHub
git remote -v | grep github. com

# Check branch protection (should be done via GitHub UI)
# - Require pull request reviews
# - Require status checks to pass
# - Require branches to be up to date
```

### GitHub Secrets Configuration
Required secrets in GitHub repository settings:
- [ ] `SLACK_WEBHOOK` (for notifications)
- [ ] `CODECOV_TOKEN` (optional, for private repos)
- [ ] Deployment secrets (if deploying)

**Validation:**
- [ ] Repository is on GitHub
- [ ] Secrets configured
- [ ] Branch protection enabled (recommended)

## 🧪 Manual Validation Steps

### Step 1: Validate Workflow Syntax

```bash
# Install GitHub CLI (if not installed)
# Mac: brew install gh
# Linux:  https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Login to GitHub
gh auth login

# Validate workflow files
echo "Validating workflow files..."

for workflow in .github/workflows/*.yml; do
    echo "Checking $workflow..."
    
    # Check YAML syntax
    python -c "import yaml; yaml.safe_load(open('$workflow'))" && \
        echo "✅ $workflow:  Valid YAML" || \
        echo "❌ $workflow: Invalid YAML"
done
```

**Validation:**
- [ ] All workflow files have valid YAML syntax
- [ ] No syntax errors reported
- [ ] Files are properly formatted

---

### Step 2: Test Local CI Runner

```bash
# Run local CI checks
./scripts/run_ci_locally. sh

# Expected output:
# ✅ ALL CI CHECKS PASSED!
# Ready to push!  🚀
```

**Validation:**
- [ ] Script executes without errors
- [ ] All checks pass locally
- [ ] Code formatting validated
- [ ] Import sorting validated
- [ ] Linting passed
- [ ] Type checking completed
- [ ] Security scan passed
- [ ] Unit tests passed
- [ ] Documentation validated

**If issues found:**
```bash
# Fix formatting
black src/monitoring/ tests/

# Fix import sorting
isort src/monitoring/ tests/

# Fix linting issues
ruff check src/monitoring/ tests/ --fix

# Re-run CI
./scripts/run_ci_locally.sh
```

---

### Step 3: Install and Test Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks on all files
pre-commit run --all-files

# Expected output:
# black.... ................................................................ Passed
# isort.................................................................... Passed
# ruff. ....................................................................Passed
# trailing-whitespace...... ................................................ Passed
# end-of-file-fixer........ ................................................Passed
# ...  (more checks)
```

**Validation:**
- [ ] Pre-commit installed successfully
- [ ] Hooks installed
- [ ] All hooks pass on existing files
- [ ] Hooks run automatically on commit

**Test automatic execution:**
```bash
# Make a small change
echo "# Test" >> test_file.py

# Try to commit
git add test_file.py
git commit -m "test:  pre-commit hooks"

# Hooks should run automatically
# If they fail, commit will be rejected
```

---

### Step 4: Trigger Workflow via Push

```bash
# Create a test branch
git checkout -b test/ci-validation

# Make a small change
echo "# CI Test" >> docs/CI_TEST.md
git add docs/CI_TEST. md
git commit -m "test: validate CI pipeline"

# Push to trigger workflows
git push origin test/ci-validation

# Monitor workflow execution
gh run list --branch test/ci-validation

# Watch workflow in real-time
gh run watch
```

**Validation:**
- [ ] Push triggers workflows
- [ ] Workflows appear in GitHub Actions tab
- [ ] All jobs start executing
- [ ] No immediate failures

**Check GitHub Actions UI:**
1. Go to: `https://github.com/YOUR_ORG/YOUR_REPO/actions`
2. Find the workflow run
3. Verify all jobs are running/completed

---

### Step 5: Create Test Pull Request

```bash
# Create PR from test branch
gh pr create \
    --title "test: validate CI/CD pipeline" \
    --body "Testing CI/CD pipeline validation" \
    --base main \
    --head test/ci-validation

# Get PR number
PR_NUMBER=$(gh pr list --head test/ci-validation --json number --jq '.[0].number')

# Watch PR checks
gh pr checks $PR_NUMBER --watch
```

**Validation:**
- [ ] PR created successfully
- [ ] PR validation workflow triggers
- [ ] Monitoring CI workflow triggers
- [ ] All required checks appear
- [ ] PR title validation passes

**Expected Checks:**
- ✅ Code Quality
- ✅ Unit Tests
- ✅ Integration Tests
- ✅ Documentation
- ✅ Docker Build
- ✅ PR Validation

---

### Step 6: Verify Individual Jobs

#### Job 1: Code Quality

```bash
# Check code quality job
gh run view --job "Code Quality"

# Expected steps:
# ✅ Checkout code
# ✅ Set up Python
# ✅ Install dependencies
# ✅ Check code formatting (Black)
# ✅ Check import sorting (isort)
# ✅ Lint code (Ruff)
# ⚠️  Type checking (MyPy) - may have warnings
# ✅ Security scan (Bandit)
```

**Validation:**
- [ ] Black formatting passes
- [ ] isort passes
- [ ] Ruff linting passes
- [ ] Bandit security scan passes
- [ ] Security report artifact uploaded

---

#### Job 2: Unit Tests

```bash
# Check unit tests job
gh run view --job "Unit Tests"

# Expected output includes:
# - Test summary
# - Coverage report
# - Coverage threshold check (≥85%)
```

**Validation:**
- [ ] All unit tests pass
- [ ] Coverage ≥85%
- [ ] Coverage report uploaded
- [ ] JUnit XML generated
- [ ] Coverage comment on PR (if PR)

**Check Coverage:**
```bash
# View coverage in PR
gh pr view $PR_NUMBER --comments | grep -A 10 "Coverage"
```

---

#### Job 3: Integration Tests

```bash
# Check integration tests job
gh run view --job "Integration Tests"

# Verify services started: 
# - Prometheus
# - Grafana  
# - Redis
```

**Validation:**
- [ ] All services started successfully
- [ ] Services health checks passed
- [ ] Integration tests executed
- [ ] All integration tests passed
- [ ] Test results uploaded

---

#### Job 4: Load Tests

**Note:** Only runs on push to main/develop, not PRs

```bash
# Check if load tests ran (on main/develop push)
gh run list --workflow "Monitoring CI/CD" --branch main | head -5

# View load test job
gh run view --job "Load Tests"
```

**Validation:**
- [ ] Load tests trigger on push (not PR)
- [ ] Application starts successfully
- [ ] Load tests execute
- [ ] Performance targets met
- [ ] Load test results uploaded

---

#### Job 5: Documentation Validation

```bash
# Check documentation validation
gh run view --job "Documentation"

# Expected: 
# ✅ Markdown linting
# ✅ Link checking
# ✅ Documentation validation script
```

**Validation:**
- [ ] Markdown files lint correctly
- [ ] No broken links found
- [ ] Documentation validation passes

---

#### Job 6: Docker Build

```bash
# Check Docker build job
gh run view --job "Docker Build"

# Expected: 
# ✅ Docker Buildx setup
# ✅ Image builds successfully
# ✅ Image tested
```

**Validation:**
- [ ] Docker image builds
- [ ] Build uses cache
- [ ] Image runs successfully
- [ ] No build errors

---

### Step 7: Verify Artifacts

```bash
# List artifacts from latest run
gh run view --log

# Download specific artifacts
gh run download --name security-report
gh run download --name unit-test-results
gh run download --name integration-test-results

# Verify artifacts
ls -lh
cat security-report/bandit-report.json | jq '.metrics'
```

**Validation:**
- [ ] Security report artifact exists
- [ ] Unit test results artifact exists
- [ ] Integration test results artifact exists
- [ ] Artifacts contain valid data

---

### Step 8: Test Deployment Workflows

**Note:** Only for staging/production branches

#### Staging Deployment

```bash
# Merge test PR to develop
git checkout develop
git merge test/ci-validation
git push origin develop

# Watch deployment
gh run list --workflow "Monitoring CI/CD" --branch develop
gh run watch

# Check deployment status
gh run view --job "Deploy to Staging"
```

**Validation:**
- [ ] Deployment triggers on develop push
- [ ] Deployment job runs
- [ ] Smoke tests execute
- [ ] Notification sent (if configured)

---

#### Production Deployment

```bash
# Merge to main (requires PR and approvals)
gh pr create \
    --title "chore: deploy to production" \
    --body "Deploying validated changes" \
    --base main \
    --head develop

# After approval and merge
gh run list --workflow "Monitoring CI/CD" --branch main
gh run view --job "Deploy to Production"
```

**Validation:**
- [ ] Deployment requires approval
- [ ] All prerequisite jobs pass
- [ ] Deployment executes
- [ ] Smoke tests pass
- [ ] Deployment status updated
- [ ] Notification sent

---

### Step 9: Test Scheduled Workflows

```bash
# Manually trigger nightly build
gh workflow run "Nightly Build"

# Wait a moment, then check
gh run list --workflow "Nightly Build"

# View results
gh run view
```

**Validation:**
- [ ] Workflow can be triggered manually
- [ ] Extended tests run
- [ ] Performance benchmarks execute
- [ ] Security audit completes
- [ ] Notification sent

---

### Step 10: Verify Dependabot

```bash
# Check Dependabot configuration
cat .github/dependabot.yml

# Check for Dependabot PRs
gh pr list --author "app/dependabot"

# Expected:  PRs for dependency updates
```

**Validation:**
- [ ] Dependabot configuration valid
- [ ] Dependabot creating PRs for updates
- [ ] PRs trigger CI checks
- [ ] Updates are scoped correctly

---

## 📊 Automated Validation Script

### File: `scripts/validate_cicd.sh`

```bash
#!/bin/bash
#
# Automated CI/CD Pipeline Validation
#

set -e

echo "🔍 Validating CI/CD Pipeline"
echo "============================="
echo ""

FAILED=0

# Test 1: Check workflow files exist
echo "Test 1: Workflow Files"
REQUIRED_WORKFLOWS=(
    ".github/workflows/monitoring-ci.yml"
    ".github/workflows/pr-validation.yml"
    ".github/workflows/nightly-build.yml"
)

for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo "✅ $workflow exists"
    else
        echo "❌ $workflow missing"
        ((FAILED++))
    fi
done
echo ""

# Test 2: Validate YAML syntax
echo "Test 2: YAML Syntax"
for workflow in . github/workflows/*.yml; do
    if python -c "import yaml; yaml. safe_load(open('$workflow'))" 2>/dev/null; then
        echo "✅ $(basename $workflow): Valid"
    else
        echo "❌ $(basename $workflow): Invalid"
        ((FAILED++))
    fi
done
echo ""

# Test 3: Check required files
echo "Test 3: Required Configuration Files"
REQUIRED_FILES=(
    ".markdownlint.json"
    ".codecov.yml"
    ".pre-commit-config.yaml"
    "scripts/run_ci_locally.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        ((FAILED++))
    fi
done
echo ""

# Test 4: Check script permissions
echo "Test 4: Script Permissions"
if [ -x "scripts/run_ci_locally.sh" ]; then
    echo "✅ run_ci_locally.sh is executable"
else
    echo "❌ run_ci_locally. sh not executable"
    ((FAILED++))
fi
echo ""

# Test 5: Run local CI
echo "Test 5: Local CI Execution"
if ./scripts/run_ci_locally.sh > /tmp/ci_output.log 2>&1; then
    echo "✅ Local CI passed"
else
    echo "❌ Local CI failed"
    echo "Check /tmp/ci_output.log for details"
    ((FAILED++))
fi
echo ""

# Test 6: Pre-commit hooks
echo "Test 6: Pre-commit Hooks"
if command -v pre-commit &> /dev/null; then
    if pre-commit run --all-files > /tmp/precommit_output.log 2>&1; then
        echo "✅ Pre-commit hooks pass"
    else
        echo "⚠️  Pre-commit hooks have issues"
        echo "Check /tmp/precommit_output.log"
    fi
else
    echo "⚠️  Pre-commit not installed"
    echo "Install with: pip install pre-commit"
fi
echo ""

# Test 7: GitHub CLI available
echo "Test 7: GitHub CLI"
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI installed"
    
    # Check authentication
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated"
        echo "Run:  gh auth login"
    fi
else
    echo "⚠️  GitHub CLI not installed"
    echo "Install from: https://cli.github.com/"
fi
echo ""

# Test 8: Check latest workflow runs
echo "Test 8: Recent Workflow Runs"
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    RECENT_RUNS=$(gh run list --limit 5 --json conclusion --jq '.[]. conclusion' 2>/dev/null | grep -c "success" || echo 0)
    
    if [ "$RECENT_RUNS" -gt 0 ]; then
        echo "✅ Recent workflow runs: $RECENT_RUNS successful"
    else
        echo "⚠️  No recent successful runs"
    fi
else
    echo "⚠️  Cannot check workflow runs (GitHub CLI not configured)"
fi
echo ""

echo "============================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
```

Make executable:
```bash
chmod +x scripts/validate_cicd.sh
```

## 🧪 Run Validation

```bash
# Run automated validation
./scripts/validate_cicd.sh

# Expected output:
# ✅ ALL VALIDATIONS PASSED
```

---

## 📋 Validation Checklist

### Configuration
- [ ] All workflow files created
- [ ] YAML syntax valid
- [ ] Configuration files present
- [ ] Scripts executable
- [ ] Pre-commit hooks configured

### Local Execution
- [ ] Local CI runner works
- [ ] Pre-commit hooks functional
- [ ] All checks pass locally

### GitHub Integration
- [ ] Workflows visible in Actions tab
- [ ] Workflows trigger on push
- [ ] Workflows trigger on PR
- [ ] Required checks appear on PRs

### Job Execution
- [ ] Code quality job passes
- [ ] Unit tests job passes
- [ ] Integration tests job passes
- [ ] Documentation validation passes
- [ ] Docker build succeeds
- [ ] Load tests execute (on push)

### Artifacts & Reports
- [ ] Security reports generated
- [ ] Test results uploaded
- [ ] Coverage reports available
- [ ] Coverage commented on PRs

### Deployments
- [ ] Staging deployment works
- [ ] Production deployment requires approval
- [ ] Smoke tests execute
- [ ] Notifications sent

### Scheduled Jobs
- [ ] Nightly build can be triggered
- [ ] Extended tests run
- [ ] Performance benchmarks execute
- [ ] Security audits complete

### Dependencies
- [ ] Dependabot configured
- [ ] Dependency PRs created
- [ ] CI runs on dependency PRs

---

## 🐛 Common Issues & Solutions

### Issue:  Workflow not triggering

**Check:**
```bash
# Verify trigger paths
cat .github/workflows/monitoring-ci.yml | grep -A 5 "on:"

# Check if files match trigger paths
git diff --name-only HEAD~1
```

**Solution:**
- Ensure changed files match `paths: ` in workflow
- Check branch names match trigger branches
- Verify workflow file is in `.github/workflows/`

---

### Issue: Job fails on GitHub but passes locally

**Check:**
```bash
# View job logs
gh run view --log --job "Job Name"

# Compare environments
echo "Local Python:" $(python --version)
echo "Local OS:" $(uname -a)
```

**Solution:**
- Check Python version matches (3.11)
- Verify all dependencies in requirements.txt
- Check for environment-specific code
- Review job logs for specific errors

---

### Issue: Services don't start in integration tests

**Check job logs:**
```yaml
# Add debugging to workflow
- name: Debug services
  run: |
    docker ps
    curl -v http://localhost:9090/-/healthy
    curl -v http://localhost:3000/api/health
```

**Solution:**
- Increase health check retries
- Add longer wait times
- Check service ports are correct
- Verify health check URLs

---

### Issue: Tests timeout

**Solution:**
```yaml
# Increase timeout in workflow
- name: Run tests
  timeout-minutes: 30  # Increase from default
  run: pytest tests/
```

Or in pytest:
```python
@pytest.mark.timeout(600)
def test_long_running():
    pass
```

---

### Issue: Coverage not uploaded

**Check:**
```bash
# Verify coverage file exists
ls -la coverage. xml

# Check Codecov token (private repos)
echo $CODECOV_TOKEN
```

**Solution:**
- Ensure `coverage.xml` is generated
- Add `CODECOV_TOKEN` secret for private repos
- Check Codecov action version is latest

---

### Issue: Deployment requires approval but none configured

**Setup approvals:**
1. Go to: Settings → Environments
2. Select environment (staging/production)
3. Check "Required reviewers"
4. Add reviewers
5. Save

---

### Issue: Pre-commit hooks slow

**Solution:**
```yaml
# Add to .pre-commit-config.yaml
default_stages:  [commit]  # Don't run on push

# Or skip specific hooks
SKIP=mypy,ruff git commit -m "message"
```

---

## 📈 Performance Benchmarks

### Expected CI Execution Times

| Job | Expected Duration | Acceptable Range |
|-----|-------------------|------------------|
| Code Quality | 2-3 min | <5 min |
| Unit Tests | 3-5 min | <10 min |
| Integration Tests | 5-7 min | <15 min |
| Load Tests | 8-10 min | <20 min |
| Documentation | 1-2 min | <5 min |
| Docker Build | 3-5 min | <10 min |
| **Total Pipeline** | **20-30 min** | **<60 min** |

---

## ✅ Sign-Off

**Implementation Status:** ⬜ Complete | ⬜ Issues Found

**Validation Results:**
```
Workflow Files:         [✅/❌]
YAML Syntax:           [✅/❌]
Local CI:             [✅/❌]
Pre-commit Hooks:     [✅/❌]
GitHub Integration:    [✅/❌]
Job Execution:        [✅/❌]
Artifacts:            [✅/❌]
Deployments:          [✅/❌]
```

**CI/CD Metrics:**
```
Average Pipeline Duration: ___ minutes
Success Rate:              ___%
Test Coverage:            ___%
```

**Issues:**
```
[List any issues found]
```

**Validated By:** ________________  
**Date:** ________________  
**Approved:** ⬜ YES | ⬜ NO

---

## 📚 Additional Resources

### GitHub Actions Documentation
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Contexts and expressions](https://docs.github.com/en/actions/reference/context-and-expression-syntax-for-github-actions)
- [Environment variables](https://docs.github.com/en/actions/reference/environment-variables)

### Useful GitHub CLI Commands
```bash
# List workflows
gh workflow list

# Run workflow manually
gh workflow run "workflow-name"

# View workflow runs
gh run list --limit 10

# Watch live run
gh run watch

# Download artifacts
gh run download <run-id>

# View run logs
gh run view <run-id> --log

# Cancel run
gh run cancel <run-id>
```

### Debugging Tips
```yaml
# Add debugging step to workflow
- name: Debug
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "Actor: ${{ github.actor }}"
    env
    pwd
    ls -la
```

---

**Next Steps:**
1. Fix any validation issues
2. Run full test suite
3. Create test PR to verify all workflows
4. Document any environment-specific setup
5. Train team on CI/CD usage
```
