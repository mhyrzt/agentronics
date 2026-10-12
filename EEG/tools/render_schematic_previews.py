"""Render exported schematic SVGs and deterministic teaching excerpts.
Run after: kicad-cli sch export svg -o exports/previews hardware/EEG.kicad_sch
Requires rsvg-convert (librsvg). Does not alter CAD files.
"""
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parents[1] / "exports" / "previews"
ET.register_namespace("", "http://www.w3.org/2000/svg")
for source in sorted(base.glob("EEG*.svg")):
    subprocess.run(["rsvg-convert", "-w", "3000", "-o", str(source.with_suffix(".png")), str(source)], check=True)

# Bounds are in schematic millimetres. Excerpts preserve the actual KiCad glyphs.
excerpts = {
    "input-channel": ("Inputs", 25, 58, 178, 103),
    "adc-core": ("Frontend", 22, 26, 150, 133),
    "adc-support": ("Frontend", 182, 40, 155, 117),
    "bias-feedback": ("Frontend", 315, 115, 80, 65),
    "battery-power": ("Power", 25, 10, 365, 55),
    "buck-supply": ("Power", 25, 65, 340, 95),
    "analog-supply": ("Power", 25, 155, 340, 96),
    "controller-header": ("Controller", 22, 23, 200, 230),
    "battery-monitor": ("Controller", 225, 145, 175, 120),
}
# Borderless exports keep title blocks out of the learning excerpts.
with tempfile.TemporaryDirectory(prefix="eeg-schematic-excerpts-") as folder:
    clean = Path(folder)
    schematic = base.parents[1] / "hardware" / "EEG.kicad_sch"
    subprocess.run(["kicad-cli", "sch", "export", "svg", "--exclude-drawing-sheet", "-o", str(clean), str(schematic)], check=True)
    ns = "{http://www.w3.org/2000/svg}"
    for name, (sheet, x, y, width, height) in excerpts.items():
        root = ET.parse(clean / ("EEG-" + sheet + ".svg")).getroot()
        root.set("viewBox", f"{x} {y} {width} {height}")
        root.set("width", f"{width}mm")
        root.set("height", f"{height}mm")
        if name == "adc-support":
            # Preserve all VCAP/reference components while excluding the adjacent
            # bias-feedback label in the otherwise empty lower-right corner.
            contents = list(root)
            for element in contents:
                root.remove(element)
            ET.SubElement(root, ns + "rect", {"x": str(x), "y": str(y), "width": str(width), "height": str(height), "fill": "#f5f4ef"})
            definitions = ET.SubElement(root, ns + "defs")
            clip = ET.SubElement(definitions, ns + "clipPath", {"id": "support-region", "clipPathUnits": "userSpaceOnUse"})
            ET.SubElement(clip, ns + "rect", {"x": "182", "y": "40", "width": "155", "height": "72"})
            ET.SubElement(clip, ns + "rect", {"x": "182", "y": "112", "width": "133", "height": "45"})
            group = ET.SubElement(root, ns + "g", {"clip-path": "url(#support-region)"})
            group.extend(contents)
        target = base / (name + ".svg")
        ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
        subprocess.run(["rsvg-convert", "-w", "2000", "-o", str(target.with_suffix(".png")), str(target)], check=True)
print("Rendered six full schematic pages and nine circuit excerpts.")
