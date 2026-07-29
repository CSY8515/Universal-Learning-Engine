# Universal Learning Engine v1.06 Localization & User Experience

## Status

Implemented localization and user-experience contract. Learning behavior,
World flow, visual structure, and the state schema remain compatible with
v1.05.

## Objective

Present the complete nine-World learning application in consistent Korean,
remove developer-oriented output from learner screens, improve BYOK guidance,
and give learners safe control over their stored records.

## Localization contract

- Navigation, headings, controls, descriptions, validation, errors, reports,
  difficulty names, challenge modes, and generated system labels are displayed
  in Korean.
- Stable internal identifiers remain unchanged for persisted-data and test
  compatibility.
- Existing English system-generated labels are translated when rendered.
- User-authored topics, notes, and generated learning content are not rewritten.

## User-data management

- Selective deletion supports multiple records and removes dependent generated
  resources, activities, and links.
- Category deletion clears one approved record category through the same
  validated deletion path.
- All-record deletion clears learning evidence while preserving subjects and
  default settings.
- Full reset restores all durable data and settings to defaults and removes the
  current session-only BYOK value.
- Destructive actions remain disabled until an explicit checkbox or exact
  confirmation phrase is supplied.

## BYOK experience

- Learners can register, replace, delete, and test their own connection key.
- The key remains only in current Streamlit session memory.
- Key deletion requires a separate confirmation checkbox.
- Missing or failed AI configuration affects only AI-dependent actions.

## Learner-visible safety

Learner screens do not expose storage identifiers, raw backup data, parser
details, provider payloads, stack traces, debug output, obsolete routing, test
doubles, or unfinished labels. Invalid backups and generated responses use
sanitized Korean guidance.

## Automated evidence

- Python compilation: PASS
- Unit, integration, Streamlit, and regression tests: 145 PASS
- Nine-World Korean presentation checks: PASS
- Selective and cascading deletion checks: PASS
- All-record preservation and full-reset checks: PASS
- BYOK deletion confirmation check: PASS
- Git whitespace validation: PASS

## Non-goals

- New learning functionality or algorithms
- UI redesign, layout replacement, or new background art
- Hover, Animation, or Glass changes
- State-schema replacement or destructive migration
- Developer-owned or durably stored API keys
- Changes to Expansion or Living OS boundaries
