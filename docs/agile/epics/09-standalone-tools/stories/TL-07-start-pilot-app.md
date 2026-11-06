# TL-07 — Preserve integrated Studio startup

**Status:** Draft; compatibility verification after EP-02.
**Epic:** [EP-09](../EPIC.md)

**As a Studio operator**, I want the existing single application to start and expose its full navigation, so that CLI additions do not fragment the user experience.

## Acceptance — Given / When / Then

**Given** an EP-02-migrated installation **when** Studio is started using its supported launcher (`make start` and packaged app where applicable) **then** one `studio/app.py` shell registers the component-owned routes and presents the existing tool navigation.

**Given** Pack, Claims, Check, Compile and Review journeys **when** used from Studio **then** they use their owner routers and preserve verified behavior.

**Given** EP-09 CLI work **when** completed **then** it does not require `pilot_app`, independent component GUI processes or a second HTTP shell.

This is a regression/compatibility story, not a new GUI product or launcher redesign.
