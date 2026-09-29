# 06_RELEASES

Each owner-accepted milestone gets a release (Constitution, Dual-Layer rule; KTA-004). A release consists of:
- a folder `06_RELEASES/<release-id>/` with the release notes, the portable bundle `<release-id>.zip` and its `.sha256` file;
- a Git tag `<release-id>`;
- a Drive release folder with the same bundle, uploaded manually by the owner while option B is in effect.

`RELEASE_LOG.md` records the bundle hash and the source commit for every release.

## Verify a bundle
```
sha256sum -c KTA-REL-0.1.zip.sha256
unzip KTA-REL-0.1.zip && python3 KTA_RELEASE_KTA-REL-0.1/tools/verify_release.py KTA_RELEASE_KTA-REL-0.1
```

## Manual Drive upload (option B)
1. In the KTA Drive folder, create `Releases/KTA-REL-0.1/` and upload `KTA-REL-0.1.zip`, `KTA-REL-0.1.zip.sha256` and `RELEASE_NOTES.md`.
2. Update the canonical Drive governance documents from the bundle (files inside the zip):
   - **KTA MASTER BLUEPRINT** (Google Doc): replace its content with `01_AUTHORITY/KTA_MASTER_BLUEPRINT_v0.1.md`.
   - **KTA PROJECT CONSTITUTION** (Google Doc): replace its content with `01_AUTHORITY/KTA_PROJECT_CONSTITUTION_v0.1.md`.
   - **KTA CURRENT STATE** (Google Doc): replace its content with `02_STATE/KTA_CURRENT_STATE.md`.
   - **KTA REGISTRIES** (Google Sheet): import `04_REGISTRIES/KTA_REGISTRIES_v0.1.xlsx` (File → Import → Replace spreadsheet), or add the new rows listed in `04_REGISTRIES/KTA_REGISTRIES_v0.1_RENDERED.md`.
3. Tell Claude "Drive upload for KTA-REL-0.1 done". Claude then marks the Drive mirror CONFIRMED in `RELEASE_LOG.md` and `SOURCE_MANIFEST_v0.1.md`.
