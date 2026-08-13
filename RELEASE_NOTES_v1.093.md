# Universal Learning Engine v1.093

## Original UI Composition Recovery

v1.093 restores the approved original Learning Engine composition after the
v1.092 viewport interpretation enlarged and cropped the Home scene.

### Fixed

- Restored the complete 16:9 Home composition so the central dome and all nine
  functional domes remain visible without cropping.
- Restored the Home navigation below the scene and kept both scene and dock
  inside the browser viewport.
- Restored functional Worlds to their original long-form left content and
  fixed right-side dedicated background composition.
- Removed the artificial internal scroll cap from functional glass content.
- Preserved the requested removal of redundant World-category copy.

### Preserved

- Theme Contract and Theme World asset mapping
- All internal route and feature identifiers
- Learning flow, CRUD, Database, API, BYOK, Analytics, Report, Expansion, and
  operational subsystems

### Validation

- Full automatic regression suite
- Streamlit localhost health check
- Browser layout measurement for the complete Home scene and dock
- Browser verification of the Management long-form split screen
- Production smoke check after deployment
