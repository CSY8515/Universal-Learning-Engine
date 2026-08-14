# Universal Learning Engine v1.097

## Background Restoration Hotfix

v1.097 corrects the out-of-scope background and Theme changes that were
included in v1.096 while preserving the intended AI connection and
subject-management layout consistency.

### Restored

- Approved Theme propagation and query-contract handling
- Original Home Theme World rendering and repository-owned world-map detail
- Layered Theme World and dedicated `w01`-`w09` feature backgrounds
- Feature motifs, inherited visual effects, and Theme-aware navigation context
- Existing responsive background and bottom-navigation behavior

### Preserved

- AI connection key registration, connection test, deletion, and consent flow
- Subject creation and management
- Left functional content, right ULE visual area, and bottom navigation layout
- Learning Engine, data, CRUD, BYOK, Analytics, reports, and user records

### Validation

- Background and Theme implementation matches the approved pre-v1.096 state
- Home, Analytics, Management, and target-page browser smoke
- Python compilation and full automated regression suite
- Localhost and production health checks
