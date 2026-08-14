# Universal Learning Engine v1.096

## AI Connection / Subject Management Layout Consistency Patch

### Layout consistency

- Aligned the AI connection and subject-management presentation with the
  existing Analytics and Management feature-page language.
- Preserved the shared split composition: functional content on the left,
  repository-owned ULE concept art on the right, and compact navigation at the
  bottom.
- Reused the existing `w08` Management background and common feature-content
  sizing without introducing a new screen, component system, or visual theme.

### Original UI recovery

- Restored the repository-owned Home World and nine dedicated feature
  backgrounds without Theme World scene replacement or floating icon layers.
- Kept the approved Home sizing, Korean navigation labels, animations, and
  existing functional panels.

### Preserved behavior

- API-key registration, replacement, connection test, and confirmed deletion.
- Subject creation and removal, settings, backup and restore, and user-data
  management.
- Learning Engine, Database, CRUD, BYOK security, Analytics, Report, routing,
  and all stored user data.

### Validation

- Python compilation and automated regression tests.
- Browser smoke checks for Home, AI connection and subject management,
  Analytics, Management, and bottom navigation.
- No critical runtime error or learner-visible markup leak.
