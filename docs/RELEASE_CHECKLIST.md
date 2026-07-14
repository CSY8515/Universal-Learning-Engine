# Release Checklist

## v0.9 local release review

- [x] Approved v0.9 boundary implemented
- [x] Existing 80 tests preserved
- [x] 10 focused v0.9 stability tests added
- [x] All 90 tests pass on local Python 3.13.14
- [x] Full Python compilation passes
- [x] Branch coverage baseline is 84%
- [x] Headless Streamlit health endpoint returns HTTP 200 and `ok`
- [x] Expansion interface version remains `0.7`
- [x] Existing UI and learning flow remain unchanged
- [x] Runtime/Loader cross-layer transitions are guarded
- [x] Session record and analytics invalidation are atomic at the application boundary
- [x] Error messages and logs exclude callback payloads and learner content
- [x] Dependency major ranges are bounded
- [x] Canonical documents are synchronized
- [ ] GitHub Actions Python 3.10 and 3.13 matrix result available after an authorized push
- [ ] Commit authorized and created
- [ ] Push authorized and completed
- [ ] Tag authorized and created
- [ ] GitHub Release authorized and published
- [ ] Deployment authorized and verified

## v1.0 design entry gate

The code and local verification baseline are ready for v1.0 design review. Official v1.0 implementation must not begin until the remaining publication-independent CI result is available and the user separately approves a v1.0 scope. v1.0 must decide whether it is a formalization-only release or includes separately approved features.
