# ARCH-01 - HTTP handling and access checks in app

**Status:** Draft; after pilot baseline.
**Epic:** [EP-02 Modularize Curbpack Studio](../EPIC.md)

**As a developer**, I want `app/` to handle FastAPI routing, requests, tokens and access control, so that subsystem functions do not depend on the web framework.

**Accept when:**
- `app/` handles HTTP requests, authentication/authorization and dispatch to the correct page or subsystem operation.
- Protected operations enforce authorization on direct HTTP/API calls, not only when opening a GUI page.
- Subsystem domain functions do not import FastAPI or depend on HTTP request/session objects.
- Previously supported routes and access behavior continue to work unless separately approved.
