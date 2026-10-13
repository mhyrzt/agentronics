"""Apply the compact 60 mm Rev B grid placement; rerouting and DRC are required afterward.
Idempotent placement targets. Do not run on a finished board merely to regenerate exports.
"""
from pathlib import Path
import pcbnew
from build_schematic import children, parse, dump

base = Path(__file__).resolve().parents[1]
path = base / 'hardware/EEG.kicad_pcb'
board = pcbnew.LoadBoard(str(path))
targets = {'C16': (148.5, 93.0), 'D10': (159.5, 121.0), 'U3': (140.5, 83.0), 'C40': (171.5, 126.5), 'D3': (133.0, 99.375), 'C22': (165.5, 95.0), 'C14': (156.5, 115.0), 'C4': (140.5, 103.125), 'C21': (161.5, 95.0), 'C15': (144.5, 96.0), 'C5': (135.5, 88.0), 'D4': (133.0, 103.125), 'R26': (167.5, 108.0), 'C34': (149.5, 132.0), 'C33': (147.0, 125.2), 'R31': (158.5, 92.5), 'L1': (146.5, 83.0), 'C18': (152.5, 93.0), 'R22': (163.5, 107.0), 'L2': (129.5, 130.0), 'J2': (163.5, 80.5), 'C30': (140.5, 79.0), 'R33': (128.5, 110.625), 'U1': (148.5, 105.0), 'C35': (154.5, 126.0), 'C7': (152.5, 115.0), 'C25': (166.8, 112.0), 'D1': (133.0, 91.875), 'MH1': (122.5, 79.0), 'R23': (156.5, 111.0), 'C28': (130.5, 82.0), 'D13': (174.5, 91.0), 'C12': (160.5, 115.0), 'R35': (128.5, 114.375), 'D7': (133.0, 110.625), 'R13': (130.5, 88.0), 'R40': (176.0, 114.5), 'F2': (164.5, 121.0), 'C27': (166.5, 92.5), 'R4': (137.0, 95.625), 'R7': (128.5, 103.125), 'C37': (129.5, 125.5), 'J6': (163.5, 130.7), 'R15': (155.5, 93.0), 'C31': (152.5, 81.5), 'R16': (159.5, 99.0), 'R41': (138.5, 125.5), 'C6': (152.5, 120.0), 'D9': (133.0, 118.125), 'R37': (128.5, 118.125), 'R9': (128.5, 106.875), 'R25': (167.5, 104.0), 'R5': (128.5, 99.375), 'C32': (157.5, 82.0), 'C24': (162.5, 111.0), 'R21': (159.5, 107.0), 'D12': (173.25, 123.5), 'C8': (143.5, 88.0), 'C13': (144.5, 115.0), 'R24': (167.5, 100.0), 'R34': (137.0, 110.625), 'R17': (163.5, 99.0), 'R14': (150.5, 88.0), 'C20': (148.5, 96.0), 'C36': (154.5, 131.0), 'MH4': (174.5, 131.0), 'R8': (137.0, 103.125), 'C17': (144.5, 93.0), 'R19': (159.5, 103.0), 'C1': (140.5, 91.875), 'MH3': (174.5, 79.0), 'C2': (140.5, 95.625), 'F1': (156.5, 88.0), 'U4': (150.5, 128.0), 'R36': (137.0, 114.375), 'R42': (134.5, 125.5), 'C3': (140.5, 99.375), 'MH2': (122.5, 131.0), 'C11': (143.5, 120.0), 'R11': (128.5, 122.5), 'R39': (163.5, 116.0), 'R44': (168.5, 121.5), 'D6': (164.5, 88.0), 'R20': (163.5, 103.0), 'R6': (137.0, 99.375), 'R18': (170.5, 93.0), 'J4': (171.5, 117.0), 'J5': (170.5, 98.65), 'R3': (128.5, 95.625), 'D8': (133.0, 114.375), 'J1': (123.5, 98.75), 'D2': (133.0, 95.625), 'R45': (170.5, 89.5), 'D5': (133.0, 106.875), 'R43': (168.5, 117.5), 'C9': (147.5, 88.0), 'R32': (162.5, 92.5), 'C10': (148.5, 115.0), 'C38': (142.5, 125.5), 'U5': (135.5, 129.5), 'R10': (137.0, 106.875), 'R12': (137.0, 122.5), 'R38': (137.0, 118.125), 'D11': (142.5, 129.5), 'C19': (153.5, 96.0), 'C29': (134.5, 82.0), 'R2': (137.0, 91.875), 'R1': (128.5, 91.875)}
rotation_targets = {'C16': 0.0, 'D10': 90.0, 'U3': 0.0, 'C40': 0.0, 'D3': 0.0, 'C22': 0.0, 'C14': 90.0, 'C4': 90.0, 'C21': 0.0, 'C15': 0.0, 'C5': 0.0, 'D4': 0.0, 'R26': 90.0, 'C34': 0.0, 'C33': 90.0, 'R31': 0.0, 'L1': 0.0, 'C18': 0.0, 'R22': 90.0, 'L2': 0.0, 'J2': 0.0, 'C30': 0.0, 'R33': 0.0, 'U1': 0.0, 'C35': 90.0, 'C7': 90.0, 'C25': 0.0, 'D1': 0.0, 'MH1': 0.0, 'R23': 90.0, 'C28': 90.0, 'D13': 0.0, 'C12': 90.0, 'R35': 0.0, 'D7': 0.0, 'R13': 0.0, 'R40': 0.0, 'F2': 0.0, 'C27': 0.0, 'R4': 0.0, 'R7': 0.0, 'C37': 0.0, 'J6': 0.0, 'R15': 90.0, 'C31': 90.0, 'R16': 90.0, 'R41': 0.0, 'C6': 0.0, 'D9': 0.0, 'R37': 0.0, 'R9': 0.0, 'R25': 90.0, 'R5': 0.0, 'C32': 90.0, 'C24': 0.0, 'R21': 90.0, 'D12': 0.0, 'C8': 90.0, 'C13': 90.0, 'R24': 90.0, 'R34': 0.0, 'R17': 90.0, 'R14': 0.0, 'C20': 0.0, 'C36': 0.0, 'MH4': 0.0, 'R8': 0.0, 'C17': 0.0, 'R19': 90.0, 'C1': 90.0, 'MH3': 0.0, 'C2': 90.0, 'F1': 0.0, 'U4': 0.0, 'R36': 0.0, 'R42': 0.0, 'C3': 90.0, 'MH2': 0.0, 'C11': 90.0, 'R11': 0.0, 'R39': 0.0, 'R44': 90.0, 'D6': 0.0, 'R20': 90.0, 'R6': 0.0, 'R18': 90.0, 'J4': 0.0, 'J5': 0.0, 'R3': 0.0, 'D8': 0.0, 'J1': -90.0, 'D2': 0.0, 'R45': 0.0, 'D5': 0.0, 'R43': 90.0, 'C9': 90.0, 'R32': 0.0, 'C10': 90.0, 'C38': 0.0, 'U5': 0.0, 'R10': 0.0, 'R12': 0.0, 'R38': 0.0, 'D11': 0.0, 'C19': 0.0, 'C29': 90.0, 'R2': 0.0, 'R1': 0.0}

affected = set()
for fp in board.GetFootprints():
 ref = fp.GetReference()
 if ref in targets:
  x,y = targets[ref]
  target = pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
  if fp.GetPosition() != target or fp.GetOrientationDegrees() != rotation_targets[ref]:
   affected.update(p.GetNetCode() for p in fp.Pads() if p.GetNetCode())
   fp.SetOrientationDegrees(rotation_targets[ref])
   fp.SetPosition(target)
   if ref.startswith(('R','C','D','F','U')) and ref not in ('R45','D13'):
    field=fp.Reference();field.SetLayer(pcbnew.F_Fab);field.SetPosition(target);field.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(.6),pcbnew.FromMM(.6)));field.SetTextThickness(pcbnew.FromMM(.1))
if not any(f.GetReference()=='MH4' for f in board.GetFootprints()):
 fp=pcbnew.FootprintLoad(str(base/'hardware/EEG_Footprints.pretty'),'MountingHole_3.2mm_M3')
 fp.SetReference('MH4');fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(174.5),pcbnew.FromMM(131)));fp.SetBoardOnly(True);fp.SetExcludedFromBOM(True);fp.SetExcludedFromPosFiles(True);board.Add(fp)
# Give all mounting holes the same explicit clearance for 6 mm nonconductive hardware.
for fp in board.GetFootprints():
 if not fp.GetReference().startswith('MH'):continue
 if not any(g.GetLayer()==pcbnew.F_CrtYd for g in fp.GraphicalItems()):
  g=pcbnew.PCB_SHAPE(fp);g.SetShape(pcbnew.SHAPE_T_CIRCLE);g.SetLayer(pcbnew.F_CrtYd);g.SetWidth(pcbnew.FromMM(.05));g.SetCenter(fp.GetPosition());g.SetEnd(fp.GetPosition()+pcbnew.VECTOR2I(pcbnew.FromMM(3.25),0));fp.Add(g)
 for field in (fp.Reference(),fp.Value()):field.SetVisible(False)
pcbnew.SaveBoard(str(path),board)
tree=parse(path.read_text())
removed=0
for kind in ('segment','via','arc'):
 for item in list(children(tree,kind)):
  net=children(item,'net')
  if net and int(net[0][1]) in affected:
   tree.remove(item);removed+=1
path.write_text(dump(tree)+'\n')
board=pcbnew.LoadBoard(str(path));pcbnew.ZONE_FILLER(board).Fill(board.Zones());pcbnew.SaveBoard(str(path),board)
print('Moved groups:',len(targets),'removed routing items:',removed,'affected nets:',len(affected))
print('Rerouting required before fabrication.')
