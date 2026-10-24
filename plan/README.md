# Active story plans

One file per story: `plan/<STORY-ID>.md`, written from `TEMPLATE.md`.

The file is the board a fresh agent resumes from: scope, checkpoint, tests, and the exact next action. `impl/pilot/` holds imported pilot protocols. Do not resume those as story plans.

While the story is open, `scripts/check_story_plan.py <STORY-ID>` reads this directory (`draft`, `ready`, `checkpoint`). When the story is DONE, move the file to `impl/<STORY-ID>.md`.
