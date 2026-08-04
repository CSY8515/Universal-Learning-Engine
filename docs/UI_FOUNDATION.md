# Ultra Brain UI Foundation Interface

## Purpose

Universal Learning Engine does not provide a second customization screen.
Ultra Brain owns user customization. ULE accepts a validated presentation
mapping through `apply_official_theme(streamlit_module, theme_settings)` or the
public `UICompatibilityLayer` interface.

The interface version is `1.0`. Omitting settings selects `ule-official` and
preserves the approved official UI exactly.

## Contract shape

```python
theme_settings = {
    "theme_id": "ultra-brain-user-theme",
    "interface_version": "1.0",
    "mode": "dark",  # dark, light, or system
    "colors": {"accent": "#58a7ff"},
    "typography": {"body": "Inter, sans-serif"},
    "icons": {"family": "Symbols", "color": "#f4f7fb"},
    "surfaces": {"card_radius": "1.35rem", "card_shadow": "none"},
    "buttons": {"radius": "999px"},
    "layout": {"app_max_width": "1640px"},
    "widgets": {"radius": "1rem"},
    "animation": {"enabled": True, "easing": "ease"},
    "backgrounds": {"w01": 'url("approved-learning.png")'},
}
```

Each section is closed: unknown sections and unknown fields fail validation.
Values remain CSS-native so Ultra Brain can apply its approved token system
without ULE translating or redesigning it.

## Public interface

- `UI_FOUNDATION_INTERFACE_VERSION`
- `UltraBrainUIInterface`
- `UICompatibilityLayer`
- `get_ui_compatibility_layer()`
- `ThemeContract`, `DesignTokens`, and component/module contracts
- `ThemeRegistry` and `UIRegistry`
- `ThemeAdapter`

The host resolves settings to an immutable `ThemeContract`; the adapter emits
only the repository's closed CSS-variable set. Existing ULE CSS consumes that
set across the map, all World backgrounds, content surfaces, Streamlit widgets,
forms, buttons, tabs, metrics, headers, docks, typography, icons, layout, and
motion.

## Failure behavior

Invalid host settings raise `ThemeContractError` before any CSS is rendered.
No learner input, generated content, API key, database value, raw object, or
session state is interpolated into the style block.

## Ownership boundary

Ultra Brain owns theme selection, persistence, and user customization. ULE
owns contract validation and applying the received presentation tokens. This
foundation defines no network transport, discovery service, background sync,
or customization UI.
