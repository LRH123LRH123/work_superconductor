"""Fetch a pinned official Pb regression case, not the 2026 production tutorial."""
from pathlib import Path
import hashlib
import json
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
upstream = ROOT / "upstream"
for item in manifest["files"]:
    if not (item["source_path"].startswith("test-suite/epw_metal/")
            or item["source_path"] in {"License", "EPW/examples/pb/pp/pb_s.UPF"}):
        continue
    target = upstream / item["source_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(item["url"], timeout=30) as response:
            target.write_bytes(response.read())
    if (hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]
            or target.stat().st_size != item["bytes"]):
        raise ValueError(f"Upstream checksum failed: {item['source_path']}")

source = upstream / "test-suite/epw_metal"
for name, original in [("scf.in", "scf_epw.in"), ("nscf.in", "nscf_epw.in"), ("epw.in", "epw1.in")]:
    text = (source / original).read_text(encoding="utf-8")
    text = text.replace("pseudo_dir      = '../../pseudo/'", "pseudo_dir      = './'")
    text = "! Paths adapted 2026-10-04 from QEF/q-e qe-7.5; upstream GPL-2.0.\n" + text
    (ROOT / name).write_text(text, encoding="utf-8", newline="\n")
shutil.copy2(upstream / "EPW/examples/pb/pp/pb_s.UPF", ROOT / "pb_s.UPF")
if not (ROOT / "save").exists():
    shutil.copytree(source / "save", ROOT / "save")
for item in manifest["files"]:
    if item["source_path"].startswith("test-suite/epw_metal/save/"):
        target = ROOT / "save" / Path(item["source_path"]).relative_to("test-suite/epw_metal/save")
        if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Copied DFPT reference changed")
print("PINNED_REFERENCE_READY: SCF/NSCF/EPW inputs; DFPT is upstream reference, not recomputed")
