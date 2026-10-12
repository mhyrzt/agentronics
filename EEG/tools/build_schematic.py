"""Rebuild KiCad 9 schematics from the checked, explicit design manifest."""
import json
import math
from pathlib import Path
import re
import uuid
from copy import deepcopy

BASE = Path(__file__).resolve().parents[1] / "hardware"
class String(str):
    pass

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text)
    stack = [[]]
    for token in tokens:
        if token == '(':
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            stack.pop()
        elif token.startswith('"'):
            stack[-1].append(String(json.loads(token)))
        else:
            stack[-1].append(token)
    assert len(stack) == 1
    return stack[0][0]

def dump(node, depth=0):
    if isinstance(node, String):
        return json.dumps(str(node), ensure_ascii=False)
    if not isinstance(node, list):
        return str(node)
    if not any(isinstance(x, list) for x in node):
        return '(' + ' '.join(dump(x) for x in node) + ')'
    parts = []
    for x in node:
        if isinstance(x, list):
            parts.append('\n' + '  ' * (depth+1) + dump(x, depth+1))
        else:
            parts.append((' ' if parts else '') + dump(x))
    return '(' + ''.join(parts) + '\n' + '  '*depth + ')'

def children(n, key):
    return [x for x in n if isinstance(x, list) and x and x[0] == key]

def uid(name):
    return String(str(uuid.uuid5(uuid.NAMESPACE_URL, 'agentronics/EEG/' + name)))

def effects(hide=False):
    e = ['effects', ['font', ['size', '1.27', '1.27']]]
    if hide:
        e.append(['hide', 'yes'])
    return e

libraries = {}
def resolve(lib, name):
    if lib not in libraries:
        p = BASE/'EEG_Custom.kicad_sym' if lib == 'EEG_Custom' else Path('/usr/share/kicad/symbols')/(lib+'.kicad_sym')
        libraries[lib] = {str(x[1]): x for x in children(parse(p.read_text()), 'symbol')}
    symbol = deepcopy(libraries[lib][name])
    ext = children(symbol, 'extends')
    if ext:
        parentname = str(ext[0][1])
        parent = resolve(lib, parentname)
        overridden = {str(x[1]) for x in children(symbol, 'property')}
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == 'property' and str(x[1]) in overridden:
                continue
            if isinstance(x, list) and x[0] == 'symbol':
                x[1] = String(str(x[1]).replace(parentname+'_', name+'_', 1))
            symbol.append(x)
        symbol.remove(ext[0])
    return symbol

def pin_records(symbol):
    result = []
    for sub in children(symbol, 'symbol'):
        for pin in children(sub, 'pin'):
            at = children(pin, 'at')[0]
            number = str(children(pin, 'number')[0][1])
            result.append((number, float(at[1]), float(at[2]), float(at[3])))
    return result

def build():
    from schematic_sections import draw_sections
    manifest = json.loads((BASE/'design-manifest.json').read_text())
    rootid = uid('root')
    sheets = ('Inputs', 'Frontend', 'Power', 'USB', 'Controller')
    for sheet in sheets:
        comps = [c for c in manifest if c['sheet'] == sheet]
        tree = ['kicad_sch', ['version', '20250114'], ['generator', String('eeschema')], ['generator_version', String('9.0')], ['uuid', uid(sheet)], ['paper', String('A3')], ['title_block', ['title', String('EEG learning prototype - '+sheet)], ['date', String('2026-10-13')], ['rev', String('B - bench prototype')]]]
        cache = ['lib_symbols']
        symbols = {}
        for c in comps:
            spec = c['symbol']
            if spec not in symbols:
                lib, name = spec.split(':', 1)
                symbol = resolve(lib, name)
                symbol[1] = String(spec)
                symbols[spec] = symbol
                cache.append(symbol)
        tree.append(cache)
        pins = {}
        for c in comps:
            ref = c['reference']
            x, y = (round(c['position'][a]/1.27)*1.27 for a in ('x', 'y'))
            rotation = c.get('rotation', 0)
            symbol = symbols[c['symbol']]
            placed = ['symbol', ['lib_id', String(c['symbol'])], ['at', x, y, rotation], ['unit', '1'], ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['uuid', uid(ref)]]
            fields = {'Reference': ref, 'Value': c['value'], 'Footprint': c['footprint'], **c['properties']}
            for index, (key, value) in enumerate(fields.items()):
                fx, fy = x+3.81, y-3.81+index*2.54
                fieldangle = 0
                if rotation in (90, 270):
                    fx, fy, fieldangle = x, y-5.08+index*2.54, 90
                elif ref.startswith('D'):
                    fx, fy = x, y-7.62+index*2.54
                if c['symbol'] == 'EEG_Custom:BAV199':
                    fx, fy = x, y+5.08+index*2.54
                if ref.startswith('U'):
                    fx, fy = x, y-13.97+index*2.54
                if 'caption_position' in c:
                    fx, fy = c['caption_position']['x'], c['caption_position']['y']+index*2.54
                placed.append(['property', String(key), String(value), ['at', fx, fy, fieldangle], effects(key not in ('Reference', 'Value') or ref.startswith('#'))])
            placed.append(['instances', ['project', String('EEG'), ['path', String('/'+rootid+'/'+uid('sheet-'+sheet)), ['reference', String(ref)], ['unit', '1']]]])
            tree.append(placed)
            for pin, px, py, angle in pin_records(symbol):
                rad = math.radians(rotation)
                xx = round(x + px*math.cos(rad) - py*math.sin(rad), 5)
                yy = round(y - px*math.sin(rad) - py*math.cos(rad), 5)
                net = c['nets'].get(pin)
                if net:
                    outward = (angle+rotation+180) % 360
                    pins[(ref,pin)] = {'xy':(xx,yy),'net':net,'angle':outward}
                elif (ref == 'U1' and pin in ('17', '18', '27', '29', '64')) or (ref == 'J6' and pin in ('A6', 'B6', 'A7', 'B7', 'A8', 'B8')):
                    tree.append(['no_connect', ['at', xx, yy], ['uuid', uid(ref+'-'+pin+'-nc')]])
        handled = draw_sections(tree,pins,sheet,String,effects,uid)
        used = set()
        for (ref,pin), p in pins.items():
            if (ref,pin) in handled or (*p['xy'],p['net']) in used:
                continue
            used.add((*p['xy'],p['net']))
            xx,yy = p['xy'];labelangle=p['angle'];lr=math.radians(labelangle)
            lx=round(xx+6.35*math.cos(lr),5);ly=round(yy-6.35*math.sin(lr),5)
            tree.append(['wire',['pts',['xy',xx,yy],['xy',lx,ly]],['stroke',['width',0],['type','default']],['uuid',uid(ref+'-'+pin+'-wire')]])
            le=effects()
            if labelangle in (0,180):le.append(['justify','left' if labelangle==0 else 'right'])
            tree.append(['global_label',String(p['net']),['shape','bidirectional'],['at',lx,ly,labelangle],le,['uuid',uid(ref+'-'+pin+'-label')]])
        (BASE/(sheet+'.kicad_sch')).write_text(dump(tree)+'\n')
    root = ['kicad_sch', ['version', '20250114'], ['generator', String('eeschema')], ['generator_version', String('9.0')], ['uuid', rootid], ['paper', String('A3')], ['title_block', ['title', String('Four-channel wireless EEG learning prototype')], ['rev', String('B - bench prototype')]], ['lib_symbols']]
    layout={'Inputs':(35,50),'Frontend':(155,50),'Controller':(275,50),'Power':(95,145),'USB':(215,145)}
    descriptions={'Inputs':('Electrode connector','Four differential filters','Common reference + bias'), 'Frontend':('ADS1299-4 acquisition','250 samples/s/channel','Reference / supply bypass'), 'Controller':('Cable to external ESP32','3.3 V logic / optional power','Wi-Fi HTTP + WebSocket target'), 'Power':('Protected 2S battery input','3.3 V digital / 5 V analog','Removable enable shunt'), 'USB':('USB-C bench power only','Diode OR / analog 9 V boost','No charging / no USB data')}
    for i, sheet in enumerate(sheets):
        x,y = layout[sheet]
        root.append(['sheet', ['at', x, y], ['size', '90', '50'], ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['color', '0', '0', '0', '0']], ['uuid', uid('sheet-'+sheet)], ['property', String('Sheetname'), String(sheet), ['at', x, y-1.27, '0'], effects()], ['property', String('Sheetfile'), String(sheet+'.kicad_sch'), ['at', x, y+51.27, '0'], effects()], ['instances', ['project', String('EEG'), ['path', String('/'+rootid), ['page', String(str(i+2))]]]]])
        for j,line in enumerate(descriptions[sheet]):
            e=effects();e.append(['justify','left'])
            root.append(['text',String(line),['at',x+7.62,y+12.7+j*10.16,0],e,['uuid',uid('overview-'+sheet+'-'+str(j))]])
    for name,x,y,char in (('inputs-to-adc',140,75,'>'),('adc-to-controller',260,75,'>'),('power-to-adc',180,128,'^')):
        root.append(['text',String(char),['at',x,y,0],['effects',['font',['size',4,4]]],['uuid',uid(name)]])
    for i, line in enumerate(('4 channels + common reference + bias electrode; 250 samples/s/channel nominal.', 'Protected 2S battery, 6.4-8.4V; USB-C 5V bench adapter; external charging only.', 'External ESP32 via cable header; Wi-Fi firmware pending; USB-C is bench power only.', 'BENCH PROTOTYPE: validate using a simulator before any human connection.', 'Disconnect electrodes before charging, wired programming, or grounded instruments.')):
        e=effects();e.append(['justify','left'])
        root.append(['text', String(line), ['at', '45', 220+i*10, '0'], e, ['uuid', uid('note-'+str(i))]])
    root.append(['sheet_instances', ['path', String('/'), ['page', String('1')]]])
    (BASE/'EEG.kicad_sch').write_text(dump(root)+'\n')

if __name__ == '__main__':
    build()
