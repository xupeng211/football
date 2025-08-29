---
name: 🐛 Bug Report
about: Report a bug to help us improve the football prediction system
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: ''
---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🔬 Testing Information

**Test Coverage Impact:**

- [ ] Bug affects tested code (covered by existing tests)
- [ ] Bug affects untested code (needs new test coverage)
- [ ] Bug breaks existing tests

**Related Test Files:**

- `tests/unit/...` (if applicable)
- `tests/integration/...` (if applicable)

## 📊 Quality Metrics

**Current Test Coverage:** XX% (run `python scripts/automated_test_report.py` to check)
**Failing Tests:** X/XXX (run `make ci` to verify)

## 🔄 Reproduction Steps

1. Go to '...'
2. Click on '....'
3. Run command '....'
4. See error

**Environment:**

- OS: [e.g. Ubuntu 22.04, macOS 13, Windows 11]
- Python Version: [e.g. 3.11.9]
- Virtual Environment: [Active/Not Active]

**Reproduction Commands:**

```bash
# Example:
source scripts/activate-venv.sh
make ci
python scripts/automated_test_report.py
```

## 📷 Expected vs Actual Behavior

**Expected behavior:**
A clear description of what you expected to happen.

**Actual behavior:**
What actually happened instead.

**Screenshots/Logs:**
If applicable, add screenshots or error logs to help explain your problem.

```
[Paste error logs here]
```

## 🛠️ Debugging Information

**Have you tried these debugging steps?**

- [ ] Run `make ci` to check all quality gates
- [ ] Check test coverage with `python scripts/automated_test_report.py`
- [ ] Activate virtual environment with `source scripts/activate-venv.sh`
- [ ] Review recent changes with `git log --oneline -10`

**Additional Debug Output:**

```bash
# Please run and paste output:
python --version
pip list | grep -E "(xgboost|fastapi|pytest)"
```

## 💡 Possible Solution

If you have ideas on how to fix this bug, please describe them here.

## ✅ Acceptance Criteria

**This bug will be considered fixed when:**

- [ ] Bug is resolved and no longer reproducible
- [ ] All existing tests pass (`make ci`)
- [ ] Test coverage is maintained or improved
- [ ] Related documentation is updated (if needed)

## 🔗 Related Issues/PRs

**Related to:**

- Issue #XXX
- PR #XXX

## 📈 Priority Assessment

**Impact Level:**

- [ ] 🔴 High - Breaks core functionality
- [ ] 🟡 Medium - Affects some features
- [ ] 🟢 Low - Minor issue or edge case

**Urgency:**

- [ ] 🚨 Critical - Needs immediate fix
- [ ] ⚡ Important - Fix within 1 week
- [ ] 📅 Normal - Fix in next release

---

**Additional Context:**
Add any other context about the problem here.
