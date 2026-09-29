# SOURCE MANIFEST v0.1

Core project state was recovered from these authoritative Google Drive artifacts:

- KTA MASTER BLUEPRINT v0.1 — Drive file ID `1DUSPtH-GJmrpqwC9OcEtlyv2ymTKLBwDbc7Pv9j35SA`
- KTA CURRENT STATE — Drive file ID `15xx-WMcsnYUjldoIEfGhBPn-Ue6BpiuHkiqJiEGqPxI`
- KTA PROJECT CONSTITUTION v0.1 — Drive file ID `1duaxFvhUA7UIF5N3y3yZPasDZTO8BZY0mk_kUu47E8w`
- KTA REGISTRIES v0.1 — Drive file ID `1Gig-57nMFuv6Augk-RoEhJWhuri3GdD-qEsQnZUbAF0`

The Markdown copies are portable renderings of the current authoritative document content at handover time. The XLSX registry is an export of the native Google Sheet.

## Dual-Layer operation (KTA-004, from 2026-09-29)
- **Git** (`TayXs/Book-World-Engine`, folder `KTA/`) is the canonical active development workspace.
- **Google Drive** (the files above, plus a `Releases/` folder) is the canonical governance and release mirror and the recovery layer.
- **Operational mode: manual release (owner decision D1, option B).** Claude builds and checksums each accepted-milestone bundle, commits and tags it in Git, and hands it to the owner. The owner uploads it to Drive. Development does not wait for Drive. Switching to direct sync (option A) is operational only; the rule stays the same.
- The Drive account connected to the 2026-09-29 Claude session cannot see the file IDs above.

## Release log
| Release | Date | Git tag | Bundle | Drive mirror |
|---|---|---|---|---|
| KTA-REL-0.1 | 2026-09-29 | `KTA-REL-0.1` | `06_RELEASES/KTA-REL-0.1/` (SHA-256 in `06_RELEASES/RELEASE_LOG.md`) | PENDING owner upload |
