"""Check links, teaching outputs, notebook execution, source hashes and slide geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zipfile

import nbformat


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--existing-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    problems = []
    for file in root.rglob("*.md"):
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
            target = match.group(1).split("#", 1)[0]
            if not target or re.match(r"[a-zA-Z]+:", target):
                continue
            candidate = file.parent / unquote(target)
            if candidate.exists():
                continue
            fallback = (args.existing_root / candidate.relative_to(root)
                        if args.existing_root else None)
            if fallback is None or not fallback.exists():
                problems.append(f"Broken link: {file.relative_to(root)} -> {target}")

    example = root / "examples/01_bcs_gap"
    notebook = nbformat.read(example / "BCS入门交互教程.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    if len(cells) != 7 or any(c.execution_count is None for c in cells):
        problems.append("Notebook has unexecuted/missing code cells")
    if any(o.output_type == "error" for c in cells for o in c.outputs):
        problems.append("Notebook contains error output")
    report = json.loads((example / "results/validation.json").read_text())
    if report["max_gap_residual_below_Tc"] >= 1e-8:
        problems.append("BCS residual too large")

    resources = root / "resources"
    manifest = json.loads((resources / "source_manifest.json").read_text())
    for item in manifest["files"]:
        file = resources / item["path"]
        if digest(file) != item["sha256"] or file.stat().st_size != item["bytes"]:
            problems.append(f"Resource hash mismatch: {file}")

    qe = root / "examples/02_qe_al_smoke"
    meta = json.loads((qe / "results/test_metadata.json").read_text())
    for name, expected in meta["input_sha256"].items():
        if digest(qe / name) != expected:
            problems.append(f"Cluster input hash mismatch: {name}")
    for item in meta["cluster_source_files"]:
        if digest(qe / "results" / item["file"]) != item["source_sha256"]:
            problems.append(f"Cluster log hash mismatch: {item['file']}")
    for file in qe.glob("*.sh"):
        if b"\r" in file.read_bytes():
            problems.append(f"Cluster script must use LF: {file.name}")

    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
          "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    deck = root / "slides/BCS超导理论与计算入门.pptx"
    with zipfile.ZipFile(deck) as z:
        if z.testzip():
            problems.append("PPTX ZIP checksum error")
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        notes = [n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        if len(slides) != 33 or len(notes) != 33:
            problems.append("Expected 33 slides and 33 notes")
        size = ET.fromstring(z.read("ppt/presentation.xml")).find("p:sldSz", ns)
        width, height = int(size.attrib["cx"]), int(size.attrib["cy"])
        for name in slides:
            slide = ET.fromstring(z.read(name))
            for transform in slide.findall(".//a:xfrm", ns):
                offset, extent = transform.find("a:off", ns), transform.find("a:ext", ns)
                if offset is None or extent is None:
                    continue
                x, y = int(offset.attrib["x"]), int(offset.attrib["y"])
                w, h = int(extent.attrib["cx"]), int(extent.attrib["cy"])
                if min(x, y, w, h) < 0 or x+w > width+9144 or y+h > height+9144:
                    problems.append(f"Off-canvas slide element: {name}")
            for cell in slide.findall(".//a:tcPr", ns):
                if cell.get("anchor", "t") not in {"t", "ctr", "b", "just", "dist"}:
                    problems.append(f"Invalid table anchor: {name}")
        for name in notes:
            values = ET.fromstring(z.read(name)).findall(".//a:t", ns)
            if sum(len(v.text or "") for v in values) < 80:
                problems.append(f"Missing detailed speaker notes: {name}")
    if problems:
        raise SystemExit("\n".join(problems))
    print("PASS: links, 7 executed notebook cells, BCS residual, PDF/log hashes, LF scripts, 33 slides/notes, slide bounds.")


if __name__ == "__main__":
    main()
