---
name: Pull Request
about: Propose a change to the codebase
title: 'feat: [TICKET-ID] A brief, clear description of the change'
labels: ''
assignees: ''

---

## 📝 Changes Description

Brief description of changes made in this PR.

**Type of Change:**

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧪 Test improvement
- [ ] 🚀 Performance improvement
- [ ] 🔧 Refactoring (no functional changes)

## 🧪 Testing

**Testing Checklist:**

- [ ] All tests pass locally (`make ci`)
- [ ] Test coverage maintained or improved
- [ ] Performance tests pass (if applicable)
- [ ] Manual testing completed

**Test Coverage:**

- Current coverage: XX% (run `python scripts/automated_test_report.py`)
- Coverage change: +X% / No change / -X%
- New test files: `tests/unit/...`, `tests/integration/...`

**New Tests Added:**

- [ ] Unit tests for new functionality
- [ ] Integration tests for API changes
- [ ] Performance tests for optimization
- [ ] Regression tests for bug fixes

## 📊 Quality Checklist

**Code Quality:**

- [ ] Code formatted (`make format`)
- [ ] Linting passed (`make lint`)
- [ ] Type checking passed (`make type`)
- [ ] Security scan passed (`make security`)

**Documentation:**

- [ ] Code is self-documenting with clear variable/function names
- [ ] Complex logic includes comments
- [ ] API changes documented
- [ ] README updated (if needed)

**Performance:**

- [ ] No performance regression introduced
- [ ] New code follows performance best practices
- [ ] Database queries optimized (if applicable)
- [ ] Memory usage considered

## 📈 Impact Assessment

**Test Coverage Impact:**

- Coverage before: XX%
- Coverage after: XX%
- Target maintained: 80%+ ✅/❌

**Performance Impact:**

- [ ] 🟢 Improved - Performance enhanced
- [ ] 🟡 No impact - Performance unchanged  
- [ ] 🔴 Needs review - Potential performance concerns

**Breaking Changes:**

- [ ] ✅ No breaking changes
- [ ] ⚠️ Has breaking changes (explain below)

**Database Changes:**

- [ ] No database changes
- [ ] Schema changes (requires migration)
- [ ] Data changes (requires data migration)

## 🔗 Related Issues

**Fixes/Addresses:**

- Closes #XXX
- Addresses #XXX
- Related to #XXX

**Dependencies:**

- Depends on PR #XXX
- Blocks PR #XXX
- Part of epic #XXX

## 🔍 Review Focus Areas

**Please pay special attention to:**

- [ ] Logic correctness in `[specific file/function]`
- [ ] Error handling in `[specific area]`
- [ ] Performance implications of `[specific change]`
- [ ] Security considerations in `[specific feature]`
- [ ] Test coverage for `[specific functionality]`

**Questions for reviewers:**

1. Question about specific implementation choice
2. Uncertainty about edge case handling
3. Request for architecture feedback

## 🚀 Deployment Considerations

**Environment Variables:**

- [ ] No new environment variables
- [ ] New variables documented in `.env.example`
- [ ] Configuration updated in deployment docs

**Dependencies:**

- [ ] No new dependencies
- [ ] New dependencies added to `requirements.txt`
- [ ] Dependencies are justified and well-maintained

**Migration Required:**

- [ ] No migrations needed
- [ ] Database migration included
- [ ] Data migration script provided
- [ ] Migration tested locally

## 📋 Pre-Merge Checklist

**Before merging, ensure:**

- [ ] All CI checks pass ✅
- [ ] Code review approved ✅
- [ ] Test coverage target met (80%+) ✅
- [ ] Documentation updated ✅
- [ ] Breaking changes documented ✅
- [ ] Performance validated ✅

**Post-Merge Actions:**

- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Monitor for issues
- [ ] Update project documentation

## 🎯 Success Criteria

**This PR will be successful when:**

1. All tests pass and coverage is maintained
2. No performance regression detected
3. Feature works as expected in staging
4. Documentation is complete and accurate

## 📷 Screenshots/Examples

**Before vs After (if applicable):**
[Add screenshots, code examples, or API responses]

**Example Usage:**

```python
# Example of how to use new functionality
from module import new_feature

result = new_feature(param="value")
```

**API Examples:**

```bash
# Example API calls for new endpoints
curl -X POST "/api/v1/new-endpoint" \
     -H "Content-Type: application/json" \
     -d '{"data": "example"}'
```

## 🔄 Testing Instructions

**How to test this PR:**

1. **Setup:**

   ```bash
   git checkout this-branch
   source scripts/activate-venv.sh
   make install
   ```

2. **Run Tests:**

   ```bash
   make ci
   python scripts/automated_test_report.py
   ```

3. **Manual Testing:**
   - Step 1: Do this
   - Step 2: Verify that  
   - Step 3: Check that result matches expected

4. **Verification:**
   - [ ] Feature works as described
   - [ ] No regression in existing functionality
   - [ ] Performance is acceptable

## 🤔 Decision Points

**Design Decisions Made:**

1. **Decision**: Chose approach A over B
   **Reason**: Better performance and maintainability

2. **Decision**: Used library X instead of Y  
   **Reason**: Better documentation and community support

**Open Questions:**

- Should we consider alternative approach Z?
- Is the current error handling sufficient?
- Do we need additional monitoring for this feature?

## 📚 Additional Context

**Research/References:**

- Link to design document
- Reference to similar implementations
- Research papers or articles consulted

**Future Improvements:**

- Potential optimizations for next iteration
- Features that could build on this work
- Known limitations to address later

---

**Reviewer Notes:**

- Estimated review time: XX minutes
- Complexity level: Low/Medium/High
- Domain knowledge required: [ML/API/DevOps/etc.]
