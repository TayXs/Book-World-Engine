"""Verify an extracted KTA release bundle against its RELEASE_MANIFEST_SHA256.json.

    python verify_release.py <extracted bundle folder>

Exit code 0 means every listed file is present with the recorded size and SHA-256, and no
unlisted files exist.
"""
import hashlib
import json
import sys
from pathlib import Path


def main(folder):
    root = Path(folder)
    manifest = json.loads((root / "RELEASE_MANIFEST_SHA256.json").read_text())
    bad, listed = [], set()
    for f in manifest["files"]:
        p = root / f["path"]
        listed.add(f["path"])
        if not p.is_file():
            bad.append(f"missing {f['path']}")
            continue
        data = p.read_bytes()
        if len(data) != f["bytes"] or hashlib.sha256(data).hexdigest() != f["sha256"]:
            bad.append(f"mismatch {f['path']}")
    extra = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
                   and str(p.relative_to(root)) not in listed and p.name != "RELEASE_MANIFEST_SHA256.json")
    bad += [f"unlisted {e}" for e in extra if "__pycache__" not in e]
    print(f"{manifest['release']} @ {manifest['source_commit'][:12]}: {len(manifest['files'])} files, "
          f"{'OK' if not bad else str(len(bad)) + ' problem(s)'}")
    for b in bad:
        print("  " + b)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
