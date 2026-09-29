# RELEASE LOG

| Release | Date | Source content commit | Git tag | Bundle SHA-256 | Drive mirror |
|---|---|---|---|---|---|
| KTA-REL-0.1 | 2026-09-29 | `34119de82164c18620b58185d09cb24dd85acb88` | `KTA-REL-0.1` *(local only; see below)* | `8359de1f81485371e486c90a478c22a6aa63d104b5bc6a357959658be9c228e6` | PENDING owner upload |

## KTA-REL-0.1 build record
- Bundle: `06_RELEASES/KTA-REL-0.1/KTA-REL-0.1.zip` (90 files, 346,665 bytes). Its root folder is `KTA_RELEASE_KTA-REL-0.1/`.
- Built with `python KTA/tools/build_release.py KTA-REL-0.1 --commit 34119de82164c18620b58185d09cb24dd85acb88`. The build is deterministic: rebuilding gives the same hash.
- Verified:
  - `sha256sum -c` → OK;
  - `verify_release.py` → 90 files OK;
  - `validate_all.py` run *inside the extracted bundle* → GREEN 5/5, 52 tests.
- **Tag status:** the annotated tag `KTA-REL-0.1` was created on commit `f4a71d4`, the commit that adds this bundle. **Pushing it was refused with HTTP 403**, because this session's Git access can push only branch `ccr-0bee19c7-psyma2`. **Owner action:** on GitHub, open Releases → Draft a new release → tag `KTA-REL-0.1` → Target → Recent commits → `f4a71d4` → Publish. The branch already contains the commit and the bundle.
- The tag points to the commit that adds this bundle. That commit's KTA content is identical to the source content commit except for `06_RELEASES/`.
