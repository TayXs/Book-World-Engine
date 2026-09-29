"""Build a checksum-verified, portable KTA release bundle from a Git commit.

    python KTA/tools/build_release.py KTA-REL-0.1 [--commit <sha>]

The build is deterministic:
  * it runs `git archive <commit> KTA/` (committed content only);
  * existing bundles (06_RELEASES/**/*.zip, *.sha256) are excluded;
  * files are added in sorted order with a fixed timestamp;
  * RELEASE_MANIFEST_SHA256.json records the release ID, the source commit, and every file's size and SHA-256.

Output: KTA/06_RELEASES/<id>/<id>.zip and <id>.zip.sha256. The script prints the bundle hash.
"""
import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

KTA = Path(__file__).resolve().parent.parent
REPO = KTA.parent
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("release_id")
    ap.add_argument("--commit", default="HEAD")
    a = ap.parse_args()
    commit = git("rev-parse", a.commit).decode().strip()
    commit_date = git("log", "-1", "--format=%cI", commit).decode().strip()
    tar = tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", commit, "KTA")))
    root = f"KTA_RELEASE_{a.release_id}"
    files = {}
    for m in tar.getmembers():
        if not m.isfile():
            continue
        rel = m.name[len("KTA/"):]
        if rel.startswith("06_RELEASES/") and (rel.endswith(".zip") or rel.endswith(".sha256")):
            continue
        files[rel] = tar.extractfile(m).read()
    manifest = {
        "release": a.release_id,
        "source_commit": commit,
        "source_commit_date": commit_date,
        "repository": "TayXs/Book-World-Engine (folder KTA/)",
        "files": [{"path": p, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} for p, b in sorted(files.items())],
    }
    files["RELEASE_MANIFEST_SHA256.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    out_dir = KTA / "06_RELEASES" / a.release_id
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{a.release_id}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            info = zipfile.ZipInfo(f"{root}/{p}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[p])
    h = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (out_dir / f"{a.release_id}.zip.sha256").write_text(f"{h}  {zpath.name}\n")
    print(json.dumps({"bundle": str(zpath.relative_to(REPO)), "sha256": h, "source_commit": commit,
                      "files": len(manifest["files"]), "bytes": zpath.stat().st_size}, indent=2))


if __name__ == "__main__":
    sys.exit(main())
