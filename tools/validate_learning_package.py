"""Check links, teaching outputs, notebook execution, source hashes and slide geometry."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zipfile

import nbformat


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_extra_deck(path, count, ns, problems):
    with zipfile.ZipFile(path) as z:
        if z.testzip():
            problems.append(f"ZIP checksum error: {path.name}")
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        notes = [n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        if len(slides) != count or len(notes) != count:
            problems.append(f"Slide/notes count mismatch: {path.name}")
        size = ET.fromstring(z.read("ppt/presentation.xml")).find("p:sldSz", ns)
        width, height = int(size.get("cx")), int(size.get("cy"))
        for name in slides:
            node = ET.fromstring(z.read(name))
            for transform in node.findall(".//a:xfrm", ns):
                offset, extent = transform.find("a:off", ns), transform.find("a:ext", ns)
                if offset is None or extent is None:
                    continue
                x, y, w, h = int(offset.get("x")), int(offset.get("y")), int(extent.get("cx")), int(extent.get("cy"))
                if min(x, y, w, h) < 0 or x+w > width+9144 or y+h > height+9144:
                    problems.append(f"Off-canvas: {path.name} {name}")
            for cell in node.findall(".//a:tcPr", ns):
                if cell.get("anchor", "t") not in {"t", "ctr", "b", "just", "dist"}:
                    problems.append(f"Invalid table anchor: {path.name} {name}")
        for name in notes:
            if sum(len(v.text or "") for v in ET.fromstring(z.read(name)).findall(".//a:t", ns)) < 80:
                problems.append(f"Insufficient notes: {path.name} {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--existing-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    problems = []
    def locate(relative):
        local = root / relative
        if local.exists():
            return local
        if args.existing_root and (args.existing_root / relative).exists():
            return args.existing_root / relative
        raise FileNotFoundError(local)
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

    example = locate("examples/01_bcs_gap")
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

    resources = locate("resources")
    manifest = json.loads((resources / "source_manifest.json").read_text())
    for item in manifest["files"]:
        file = resources / item["path"]
        if digest(file) != item["sha256"] or file.stat().st_size != item["bytes"]:
            problems.append(f"Resource hash mismatch: {file}")

    qe = locate("examples/02_qe_al_smoke")
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
    deck = locate("slides/BCS超导理论与计算入门.pptx")
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
    bdg = locate("examples/03_bdg_uniform")
    notebook = nbformat.read(bdg / "BdG入门交互教程.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    if len(cells) != 8 or any(c.execution_count is None for c in cells):
        problems.append("BdG Notebook has unexecuted/missing code cells")
    if any(o.output_type == "error" for c in cells for o in c.outputs):
        problems.append("BdG Notebook contains error output")
    report = json.loads((bdg / "results/validation.json").read_text())
    for key in ["momentum_spectrum_max_error", "hermiticity_max_error",
                "reduced_particle_hole_max_error", "paired_spectrum_max_error",
                "eigenvector_orthonormality_max_error", "eigenvector_residual_max_error",
                "single_spin_completeness_max_error"]:
        if not 0 <= report[key] < 1e-11:
            problems.append(f"BdG numeric check failed: {key}")
    if any(not 0 <= value < 1e-11 for value in report["chain_spectrum_max_errors"].values()):
        problems.append("BdG analytic chain spectrum mismatch")
    if report["minimum_positive_impurity_energy"] < abs(report["parameters"]["Delta_over_J"])-1e-11:
        problems.append("Unexpected subgap scalar impurity eigenvalue")

    cutoff = locate("examples/04_qe_al_cutoff")
    record = json.loads((cutoff / "results/cluster_record.json").read_text())
    for item in record["files"]:
        file = cutoff / item["path"]
        if digest(file) != item["sha256"] or file.stat().st_size != item["bytes"]:
            problems.append(f"Cutoff source hash mismatch: {item['path']}")
    report = json.loads((cutoff / "results/validation.json").read_text())
    for item in report["sha256"]:
        if digest(cutoff / item["path"]) != item["sha256"]:
            problems.append(f"Cutoff report/source mismatch: {item['path']}")
    rows = report["rows"]
    if [r["ecutwfc_Ry"] for r in rows] != [30, 40, 50, 60, 80]:
        problems.append("Unexpected cutoff scan grid")
    if report["job_id"] != record["job_id"] or report["lowest_tested_acceptable_Ry"] != 30:
        problems.append("Unexpected cutoff archival report")
    for row in rows:
        difference = abs(row["energy_Ry"]-rows[-1]["energy_Ry"])*13605.693122994
        if abs(difference-row["abs_difference_meV_per_atom"]) > 1e-8:
            problems.append("Incorrect cutoff energy conversion")
    for file in cutoff.rglob("*.sh"):
        if b"\r" in file.read_bytes():
            problems.append(f"Cluster script must use LF: {file.name}")
    with zipfile.ZipFile(locate("slides/BdG超导理论与计算入门.pptx")) as z:
        if z.testzip():
            problems.append("BdG PPTX ZIP checksum error")
        slides = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        notes = [n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        if len(slides) != 30 or len(notes) != 30:
            problems.append("Expected 30 BdG slides and 30 notes")
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
                    problems.append(f"Off-canvas BdG slide element: {name}")
            for cell in slide.findall(".//a:tcPr", ns):
                if cell.get("anchor", "t") not in {"t", "ctr", "b", "just", "dist"}:
                    problems.append(f"Invalid BdG table anchor: {name}")
        for name in notes:
            values = ET.fromstring(z.read(name)).findall(".//a:t", ns)
            if sum(len(v.text or "") for v in values) < 80:
                problems.append(f"Missing BdG speaker notes: {name}")
    for name in ["BCS", "BdG"]:
        pdf = locate(f"slides/{name}超导理论与计算入门.pdf")
        if not pdf.read_bytes().startswith(b"%PDF-"):
            problems.append(f"Invalid PDF: {pdf.name}")
    metal = locate("examples/05_qe_al_kmesh_smearing")
    record = json.loads((metal / "results/cluster_record.json").read_text(encoding="utf-8"))
    for item in record["files"]:
        source = metal / item["path"]
        if digest(source) != item["sha256"] or source.stat().st_size != item["bytes"]:
            problems.append(f"Metal scan source mismatch: {item['path']}")
    spec = importlib.util.spec_from_file_location("al_metal_scan", metal / "collect_results.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rebuilt = module.collect(metal)
    saved = json.loads((metal / "results/validation.json").read_text(encoding="utf-8"))
    if rebuilt != saved or saved["job_id"] != record["job_id"]:
        problems.append("Metal scan report differs from raw sources/provenance")
    notebook = nbformat.read(metal / "Al金属收敛交互教程.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    if len(cells) != 6 or any(c.execution_count is None for c in cells):
        problems.append("Metal scan Notebook has unexecuted/missing code cells")
    if any(o.output_type == "error" for c in cells for o in c.outputs):
        problems.append("Metal scan Notebook contains errors")
    for file in [metal / "submit.sh", metal / "scan_plan.json", *metal.glob("k*_s*/scf.in")]:
        if b"\r" in file.read_bytes():
            problems.append(f"Metal cluster input should use LF: {file.name}")
    check_extra_deck(locate("slides/Al金属k网格与展宽收敛入门.pptx"), 14, ns, problems)
    if not locate("slides/Al金属k网格与展宽收敛入门.pdf").read_bytes().startswith(b"%PDF-"):
        problems.append("Invalid Al slide PDF")
    from validate_epc_package import validate_package
    problems.extend(validate_package(locate("examples/06_epc_eliashberg")))
    check_extra_deck(locate("slides/电子声子耦合与Eliashberg计算入门.pptx"), 20, ns, problems)
    if not locate("slides/电子声子耦合与Eliashberg计算入门.pdf").read_bytes().startswith(b"%PDF-"):
        problems.append("Invalid EPC slide PDF")
    from validate_two_band_package import validate_package as validate_two_band
    problems.extend(validate_two_band(locate("examples/07_two_band_eliashberg")))
    check_extra_deck(locate("slides/双带与各向异性Eliashberg入门.pptx"), 20, ns, problems)
    if not locate("slides/双带与各向异性Eliashberg入门.pdf").read_bytes().startswith(b"%PDF-"):
        problems.append("Invalid two-band slide PDF")
    from validate_mgb2_data_package import validate_package as validate_mgb2_data
    problems.extend(validate_mgb2_data(locate("reproductions/02_mgb2_imaginary_gap")))
    if problems:
        raise SystemExit("\n".join(problems))
    print("PASS: links, 43 executed notebook cells, BCS/BdG/Al/EPC/two-band/MgB2-data numeric checks, "
          "resource/cluster hashes, real job identities, LF inputs, 117 slides/notes and slide bounds.")


if __name__ == "__main__":
    main()
