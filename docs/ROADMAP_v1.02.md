# Universal Learning Engine v1.02 World Integration

## Status

This document defines the v1.02 implementation contract. It is a functional
integration release and does not authorize UI redesign, publication, or
deployment.

## Preserved baseline

- Validated universal-topic lesson generation
- One-question-at-a-time CBT, scoring, feedback, and explanation
- Deterministic adaptive recommendations and Learning Analytics
- Stable Expansion API and connection-only Living OS boundary
- Repository-owned static theme and existing Streamlit components

## World contract

The functional navigation contains:

1. Learning
2. Recovery
3. Challenge
4. Analytics
5. AI
6. Planner
7. Library
8. Management
9. My Learning

Completed Learning and Challenge rounds are the shared evidence source. They
feed Recovery, Analytics, Library, Management, My Learning, and Report. AI reads
the current learning context and aggregate evidence. Planner creates explicit
learner-controlled navigation into a selected World.

## Functional scope

- Recovery queue, executable Recovery Session, answer feedback, and history
- Independent Exam, Hard, Nightmare, and mock-exam Challenge entry
- Explicit AI question, recommendation, and summary
- Today Learning, goals, and dated World schedules
- Generated learning resources, notes, and search
- Expansion status, subject management, settings, backup, and restore
- Study time, level, achievements, aggregate statistics, and report download
- Connection of direct-task and practice writing to Library notes

## Exclusions

- UI redesign or new visual system
- World background changes
- Korean copy-edit pass
- Hover, Animation, or Glass changes
- Background scheduler, notifications, or autonomous learning actions
- Remote Pack acquisition or automatic updates
- Login or multi-user account isolation
- Commit, push, release, or deployment

## Acceptance criteria

1. Existing lesson, CBT, scoring, adaptive, analytics, and Expansion tests remain
   compatible except where v1.02 intentionally replaces major navigation.
2. Each of the nine Worlds has a real functional entry.
3. Completed rounds create shared downstream evidence exactly once.
4. Recovery completion updates retained wrong-answer state.
5. Planner, Library, Management, and My Learning mutations survive reruns.
6. Backup export and restore round-trip the validated World state.
7. Dummy direct/practice inputs are connected to Library notes.
8. Local tests and localhost health verification pass before reporting.
