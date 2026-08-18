# Universal Learning Engine v1.099

## Feature Background Resolution Hotfix

v1.099 corrects Dark Theme feature-background resolution without changing the
Home World, navigation, functional UI, or learning behavior.

### Fixed

- Approved Feature contexts now activate the matching Theme package directly.
- Learning Plan resolves to its registered Dark feature artwork.
- Learning Analytics resolves to its registered Dark feature artwork.
- Every other feature resolves deterministically to its own Official `w01` to
  `w09` artwork and is reported as `ASSET REQUIRED` until dedicated Dark art is
  approved.
- Long-lived Streamlit processes refresh the feature resolver when this
  release is deployed.

### Preserved

- Home World composition and navigation
- Exact feature IDs and functional overlays
- AI connection, subject management, data, CRUD, BYOK, reports, and routing
- Existing Theme, Lock, Override, revision, and propagation architecture

### Validation

- Complete nine-feature resolution matrix
- Feature A to Feature B to Feature A determinism
- Official return and Dark re-entry
- Existing role-asset and UI-foundation regression suites
