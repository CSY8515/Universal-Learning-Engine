# Universal Learning Engine v1.07 Official UI / UX

## Goal

Present the existing Universal Learning Engine as one explorable Learning
World, following the Living OS official structure, visual language, and motion
reference without changing functional behavior.

## Presentation contract

- The home view is one central Universal Learning Engine biosphere surrounded
  by nine functional World domes.
- The central dome has a clearly recognizable small tree ornament.
- Every surrounding dome has a function-evoking symbol, botanical top detail,
  Korean label, focused Hover glow, and direct connection to its existing
  World.
- Learning, Recovery, Challenge, Analytics, AI, Planner, Library, Management,
  and My Learning each have a dedicated cinematic background and World theme.
- Existing controls render inside dark translucent Glass surfaces while the
  environment remains visible.
- World entry uses a restrained reveal transition. Motion is disabled when the
  learner requests reduced motion.
- A compact persistent World dock provides direct World-to-World and home
  navigation.

## Visual contract

- Near-black navy cosmic space
- Transparent glass biospheres and reflective surfaces
- Sapphire and cobalt learning light
- Antique brass and restrained gold botanical detail
- Cinematic fantasy realism consistent across the World map and interiors
- Korean learner-facing labels with no raw internal output

## Preserved boundary

This release changes presentation only. It does not change:

- Learning Engine or learning flow
- World-state structure or user records
- Database behavior, CRUD, backup, or restore
- API or BYOK behavior
- Analytics or Report behavior
- Expansion Platform or Living OS integration boundary

## Acceptance

- Initial World map renders without error.
- All nine functional Worlds remain independently reachable.
- Each World loads its dedicated background.
- Existing functional and regression tests pass.
- Localhost health returns `ok`.
- No developer-facing output appears in learner screens.
- Keyboard focus, responsive behavior, and reduced-motion behavior remain
  available.

Publication remains gated by automatic tests, localhost verification, and
explicit user approval.
