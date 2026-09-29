# MOBILE START HERE — Claude Code + Knowledge → Action

This package is designed so you can operate the project mostly by sending short instructions from your phone.

## What to do
1. Upload/open this ZIP as a Claude Code project/workspace.
2. Make sure the ZIP is extracted so the root `CLAUDE.md` is visible.
3. Send Claude Code the text in `FIRST_MESSAGE_TO_CLAUDE_CODE.md`.
4. After that, you should usually be able to use short messages such as:
   - `Continue from project state.`
   - `Resume the current KTA work.`
   - `Show me the material decisions that need my approval.`
   - `Checkpoint and prepare a handoff.`

You should not need to reattach the source files every session if Claude Code retains the project workspace.

## What Claude should do for you
Claude should read project state from files, work inside the workspace, keep progress updated, and save its next action before a context reset/session boundary.

It should put detailed analysis into files and keep phone-chat summaries compact.

## Refinement mode
This handover intentionally lets Claude critically review the project before it continues building.

Claude may directly make **non-material** refinements.

For **material** changes to product direction, CORE rules, CURRENT rules, market, mission, major architecture, metrics, or scope, it should collect the proposals and ask you for approval in one concise batch.

## If a new Claude session loses context
Send only:

> Read CLAUDE.md and resume KTA from PROJECT_STATE.json, PROGRESS.md, and NEXT_ACTION.md. Do not reconstruct state from chat memory.

## If you want Claude to work for a long stretch
Send:

> Continue the authorized KTA work autonomously. Preserve governance, checkpoint durable state before context transitions, and stop only at a material owner-decision boundary or when the authorized stage is complete.

## Current authorized stage
Mission Generation Engine v0.1.

The project vision is broader than this stage. Completing Lane 02 does not mean the product is finished; Claude must checkpoint the result and identify the next stage.
