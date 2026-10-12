"""Compare exported schematic nets, PCB pads and BOM; no board mutation."""
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from build_schematic import children, parse

base = Path(__file__).resolve().parents[1]
xml = ET.parse(base/'exports/EEG.net').getroot()
expected = {}
for net in xml.findall('./nets/net'):
    for n in net.findall('node'):
        expected[(n.attrib['ref'], n.attrib['pin'])] = net.attrib['name']
components = {c.attrib['ref']: c for c in xml.findall('./components/comp')}
board = parse((base/'hardware/EEG.kicad_pcb').read_text())
seen = set()
errors = []
pad_count = 0
footprints = {}
for fp in children(board, 'footprint'):
    props = {str(p[1]): str(p[2]) for p in children(fp, 'property')}
    ref = props['Reference']
    if ref.startswith('MH'):
        continue
    footprints[ref] = str(fp[1])
    for p in children(fp, 'pad'):
        pin = str(p[1])
        if not pin:
            continue  # Unnumbered solder-paste apertures in the module footprint.
        pad_count += 1
        key = ref, pin
        seen.add(key)
        nets = children(p, 'net')
        actual = str(nets[0][2]) if nets else ''
        want = expected.get(key)
        if want != actual:
            errors.append({'pad': key, 'schematic': want, 'pcb': actual})
for key in expected.keys()-seen:
    errors.append({'missing_pcb_pad': key})
for ref,c in components.items():
    if c.findtext('footprint') != footprints.get(ref):
        errors.append({'footprint_mismatch': ref})
bom = list(csv.DictReader((base/'exports/BOM.csv').open()))
quantity = sum(int(r['Quantity']) for r in bom)
if quantity != len(components):
    errors.append({'bom_quantity': quantity, 'schematic_components': len(components)})
if any(not r['MPN'] or not r['Manufacturer'] for r in bom):
    errors.append({'incomplete_bom_fields': True})
baseline=json.loads((base/'reports/baseline-net-map.json').read_text())
allowed_changes = {
    'C33:1': ('BAT_SW', 'BOOST9V'),
    'U4:1': ('BAT_SW', 'BOOST9V'),
    'U4:3': ('BAT_SW', 'BOOST9V'),
    'R31:2': ('VBAT_SENSE', 'VIN_SENSE'),
    'R32:1': ('VBAT_SENSE', 'VIN_SENSE'),
    'C27:1': ('VBAT_SENSE', 'VIN_SENSE'),
}
removed_refs = {'U2', 'J3', 'R27', 'R28', 'R29', 'R30', 'C23', 'C26', 'SW2', 'SW3'}
current = {ref+':'+pin: net for (ref,pin),net in expected.items()}
net_changes = []
for pin, before in baseline.items():
    ref = pin.split(':')[0]
    if ref in removed_refs:
        if ref in components:
            errors.append({'removed_component_still_present': ref})
        continue
    after = current.get(pin)
    if before != after:
        change = {'pin': pin, 'before': before, 'after': after}
        net_changes.append(change)
        if allowed_changes.get(pin) != (before, after):
            errors.append({'unexpected_baseline_net_change': change})
manifest = json.loads((base/'hardware/design-manifest.json').read_text())
for component in manifest:
    ref = component['reference']
    if ref.startswith('#'):
        continue
    for pin, net in component['nets'].items():
        actual = expected.get((ref, str(pin)))
        if actual != net:
            errors.append({'manifest_pin_mismatch': ref+':'+str(pin), 'intended': net, 'exported': actual})
drc = json.loads((base/'reports/final-drc.json').read_text())
for field in ('violations', 'unconnected_items', 'schematic_parity'):
    if drc[field]:
        errors.append({'drc_field': field, 'count': len(drc[field])})
result = {
    'passed': not errors,
    'electrical_components': len(components),
    'electrical_footprints': len(footprints),
    'numbered_electrical_pad_instances': pad_count,
    'unique_schematic_pins': len(expected),
    'bom_grouped_lines': len(bom),
    'bom_total_quantity': quantity,
    'intentional_revision_net_changes': net_changes,
    'removed_components': sorted(removed_refs),
    'added_components': sorted(set(components)-{key.split(':')[0] for key in baseline}),
    'errors': errors,
    'scope': 'CAD connectivity and metadata only; no assembled electrical validation',
}
(base/'reports/connectivity-audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['passed'] else 1)
