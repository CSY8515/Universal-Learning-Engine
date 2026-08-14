# Universal Learning Engine v1.098

## Dedicated Background Hotfix

v1.098 fixes the background rendering regression that allowed an obsolete
Theme blend to darken and desaturate the dedicated Feature World artwork.

### Fixed

- Dedicated `w01`-`w09` feature backgrounds render at full opacity
- Feature artwork uses normal color blending with no desaturation filter
- Current CSS is reloaded on every Streamlit rerun instead of being cached
  across deployments
- A final runtime presentation rule prevents stale deployment CSS from
  overriding the approved feature background

### Preserved

- Home World and navigation
- Left functional content and right visual layout
- AI connection and subject management behavior
- Theme contracts, Learning Engine, data, CRUD, BYOK, Analytics, and reports

### Validation

- Analytics and Management dedicated background assets
- Focused background regression tests and complete automated suite
- Localhost health and browser smoke
- Production title, background computed styles, and functional controls
