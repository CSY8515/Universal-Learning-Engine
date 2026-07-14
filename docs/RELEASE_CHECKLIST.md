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
- [x] v0.9 commit `770c7d9` exists locally
- [x] Local `origin/main` tracking reference matches the v0.9 commit
- [ ] Tag authorized and created
- [ ] GitHub Release authorized and published
- [ ] Deployment authorized and verified

## v1.0 design entry gate — complete

The user approved the production-quality completion scope. The implementation
preserves v0.9 behavior and adds the official UI, Dashboard, developer quality,
documentation, and release verification defined in `ROADMAP_v1.0.md`.

## v1.0 Stable local release review

- [x] Approved v1.0 boundary implemented
- [x] Dashboard is the initial Home view
- [x] Dashboard navigation preserves session evidence
- [x] Home and Retry clearing contracts preserved
- [x] Official dark, responsive, focus-visible, reduced-motion skin implemented
- [x] Dynamic learner content excluded from unsafe HTML/CSS interpolation
- [x] Expansion interface version remains `0.7`
- [x] Expansion primary facade compatibility test added
- [x] Compatible dependency ranges and tested direct constraints recorded
- [x] Developer Guide, Security Policy, API guide, and release review prepared
- [x] Complete local test suite passes: 101 tests
- [x] Full Python compilation passes
- [x] Branch coverage is at least 84%
- [x] Headless Streamlit health endpoint returns HTTP 200 and `ok`
- [x] Automated UI and selective-render validation passes
- [x] Performance validation recorded
- [x] Static secret and security validation passes
- [ ] Pixel-level manual browser review completed
- [ ] Python 3.10 and 3.13 remote CI evidence available
- [ ] Final user approval received
- [ ] Commit authorized and created
- [ ] Push authorized and completed
- [ ] `v1.0.0` tag authorized and created
- [ ] GitHub Release authorized and published
- [ ] Deployment authorized and verified
