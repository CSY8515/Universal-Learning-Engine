# Universal Learning Engine v1.03 Learning Flow Integration

## Status

This document defines the implemented v1.03 functional contract. It expands
the released v1.02 World state without authorizing UI redesign, publication, or
deployment.

## Preserved baseline

- Validated universal-topic lesson generation and one-question CBT
- Deterministic adaptive guidance and Learning Analytics
- Nine-World navigation and durable normalized World state
- Stable Expansion API and connection-only Living OS boundary
- Existing Streamlit controls and repository-owned static theme

## Integrated flow

```text
Learning
  -> Recovery Session, Record, History, Recommendation
  -> Challenge Session, History, Result
  -> Analytics evidence
  -> AI context and Recommendation
  -> Planner goal and Learning schedule
  -> Learning topic transfer
  -> Library multi-World records
  -> Management subjects
  -> My Learning integrated statistics
  -> Report
```

The flow remains learner controlled. Recovery recommendations and AI
recommendations expose explicit connection actions. No background action,
notification, or autonomous learning start is introduced.

## Functional contract

### Recovery

- Completed Learning or Challenge rounds create retained wrong-answer evidence.
- A Recovery Session records answers, score, duration, completion state, and
  history.
- Completion creates one deterministic Challenge recommendation.
- Accepting the recommendation transfers its mode and topic into Challenge.
- The Recovery record is stored automatically in Library.

### Challenge

- Exam, Hard, Nightmare, and mock-exam entries create independent sessions.
- Each completed session owns a distinct result linked to its source round.
- Results retain mode, topic, difficulty, score, accuracy, duration, and an
  optional source Recovery recommendation.
- Challenge results feed Analytics, Library, My Learning, and Report.

### Analytics and AI

- Integrated Analytics reads Learning, Recovery, Challenge, Planner, Library,
  AI, and Management evidence.
- AI question, recommendation, and summary prompts consume the integrated
  Analytics snapshot.
- AI output is stored in AI history and Library.
- An explicit AI Recommendation connection creates one real Planner goal and
  one real Learning schedule exactly once.

### Planner and Library

- A Learning schedule transfers its retained topic into the Learning input
  before navigation.
- Goals and schedules are stored automatically as Planner Library records.
- Library accepts normalized resources from Learning, Recovery, Challenge, AI,
  and Planner while preserving v1.02 resource compatibility.
- Topics created by Library-connected evidence are registered in Management.

### My Learning and Report

- Study time combines Learning/Challenge round duration and completed Recovery
  duration.
- Level, points, achievements, long-term counts, and World record totals use
  shared evidence across all nine Worlds.
- Report contains Learning, Recovery, Challenge, Analytics, AI, Planner,
  Library, Management, and My Learning sections.

## Legacy removal

- Removed the unused Dashboard renderer and module.
- Removed the unused Review renderer and module.
- Removed the unused shared Dashboard/Review component module.
- Removed legacy explicit-navigation metadata and callback routing.
- Removed the obsolete topic-input placeholder.

## Exclusions

- UI redesign or new visual system
- World background changes
- Hover, Animation, or Glass changes
- Background scheduler, notification, or autonomous learning
- Concrete Living OS behavior
- Commit, push, release, or deployment

## Acceptance criteria

1. All preserved tests pass.
2. Recovery produces retained records, history, and a Challenge recommendation.
3. Challenge sessions and results remain independent.
4. AI Recommendation creates an idempotent Planner goal and schedule only
   after explicit learner action.
5. Planner transfers a selected Learning topic into Learning.
6. Library contains generated evidence from every required source World.
7. My Learning and Report integrate all required World evidence.
8. No runtime Dummy, TODO, Placeholder, disconnected button, Dashboard, Review,
   or legacy routing remains.
9. Localhost health and all nine World entries pass before reporting.
