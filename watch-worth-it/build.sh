#!/usr/bin/env bash
#
# Packs the extension into dist/watch-worth-it.zip.
#
# Android browsers that support extensions (Kiwi and its relatives) install from
# a zip rather than from a folder, so this is the file you download on the phone.
# manifest.json must sit at the zip root - do not zip the containing folder.

set -euo pipefail
cd "$(dirname "$0")"

OUT="dist/watch-worth-it.zip"
mkdir -p dist

python3 - "$OUT" <<'PY'
import hashlib, json, pathlib, sys, zipfile

out = pathlib.Path(sys.argv[1])
root = pathlib.Path(".")

INCLUDE = ["manifest.json", "background.js", "content.js", "options.html", "options.css", "options.js"]
INCLUDE_DIRS = ["lib", "icons"]

files = [pathlib.Path(name) for name in INCLUDE]
for folder in INCLUDE_DIRS:
    files += sorted(p for p in pathlib.Path(folder).rglob("*") if p.is_file())

missing = [str(f) for f in files if not f.exists()]
if missing:
    sys.exit(f"missing from the build: {', '.join(missing)}")

manifest = json.loads(pathlib.Path("manifest.json").read_text())

# Deterministic: same sources in, byte-identical zip out, so a rebuild that
# changes nothing does not show up as a diff.
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        info = zipfile.ZipInfo(str(path).replace("\\", "/"), date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())

digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
print(f"{out}  v{manifest['version']}  {len(files)} files  {out.stat().st_size:,} bytes  sha256:{digest}")
PY
