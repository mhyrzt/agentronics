"""Package checked CAD deliverables, preserving the documented folder layout."""
import hashlib
import json
from pathlib import Path
import zipfile

base = Path(__file__).resolve().parents[1]
release = base / "releases"
release.mkdir(exist_ok=True)
paths = [base / "README.md", base / ".gitignore"]
for folder in ("hardware", "exports", "reports", "tools"):
    paths.extend(sorted(
        p for p in (base / folder).rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and not p.name.endswith((".kicad_prl", ".lck", ".pyc"))
        and p.name != "fp-info-cache"
        and not any(part.startswith(".mcp-backups") or part.endswith("-backups") for part in p.relative_to(base).parts)
    ))
hashes = {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
checksum = release / "SHA256SUMS.json"
checksum.write_text(json.dumps(hashes, indent=2) + "\n")
paths.append(checksum)
fabrication_dir = base / "exports" / "fabrication"
fabrication = sorted(p for p in fabrication_dir.iterdir() if p.is_file())
for filename, items, relative_base, prefix in (
    ("EEG-revB-design.zip", paths, base, "EEG/"),
    ("EEG-revB-fabrication.zip", fabrication, fabrication_dir, ""),
):
    target = release / filename
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in items:
            archive.write(p, prefix + str(p.relative_to(relative_base)))
        assert archive.testzip() is None
    print(filename, len(items), "files", target.stat().st_size, "bytes")
