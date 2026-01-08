# Documentation Validation Guide

## 🎯 Purpose

Ensure documentation is accurate, complete, and high-quality.

---

## 🚀 Quick Start

### Run All Validations

```bash
chmod +x scripts/validate_documentation.sh
./scripts/validate_documentation.sh
```

### Run Python Validator Only

```bash
python3 scripts/validate_documentation.py
```

### Run Quick Lint

```bash
./scripts/lint_docs.sh
```

---

## 📋 What Gets Validated

### 1. File Existence

- All required documentation files present
- No missing files referenced in INDEX

### 2. Markdown Syntax

- Proper header hierarchy
- Closed code blocks
- No broken formatting

### 3. Internal Links

- All internal links resolve
- All anchor links valid
- No 404 errors

### 4. Code Blocks

- Python syntax valid
- No dangerous bash commands
- Proper language tags

### 5. Consistency

- Metric names consistent
- Terminology consistent
- Format consistent

### 6. Completeness

- All required sections present
- No missing content
- No TODO markers

### 7. Commands

- Shell commands valid
- Prerequisites available

---

## 🔧 Installation

### Prerequisites

```bash
pip install markdown
npm install -g markdownlint-cli
npm install -g markdown-link-check
sudo apt-get install aspell
```

### Quick Install

```bash
./scripts/install_doc_tools.sh
```

---

## ✅ Validation Checklist

Before committing documentation changes:

- [ ] Run ./scripts/validate_documentation.sh
- [ ] All errors fixed
- [ ] Warnings reviewed
- [ ] Links tested manually
- [ ] Code examples tested
- [ ] Spelling checked
- [ ] Consistent formatting
- [ ] Table of contents updated

---

## 📊 CI Integration

Documentation is automatically validated on:

- Pull requests
- Commits to main/develop branches

Check status: GitHub Actions → "Validate Documentation"

---

## 🐛 Common Issues

### "Broken link" false positive

Add to .markdown-link-check.json:

```json
{
  "ignorePatterns": [{ "pattern": "^http://localhost" }]
}
```

### Python syntax error in code block

Check for:

- Unclosed strings/brackets
- Invalid indentation
- Missing imports in examples

### Missing section warning

Update required_sections in scripts/validate_documentation.py

---

## 📞 Getting Help

- Issues: Create GitHub issue with documentation label
- Questions: Ask in #mcp-memory-docs channel

---

**Last Updated:** 2025-01-08
