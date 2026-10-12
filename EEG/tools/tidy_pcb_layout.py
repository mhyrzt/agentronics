"""Apply the square Rev B grid placement; rerouting and DRC are required afterward.
Idempotent placement targets. Do not run on a finished board merely to regenerate exports.
"""
from pathlib import Path
import pcbnew
from build_schematic import children, parse, dump

base = Path(__file__).resolve().parents[1]
path = base / 'hardware/EEG.kicad_pcb'
board = pcbnew.LoadBoard(str(path))
targets = {
 'R1':(35,59), 'D1':(40,59), 'R2':(45,59), 'C1':(50,59),
 'R3':(35,63), 'D2':(40,63), 'R4':(45,63), 'C2':(50,63),
 'R5':(35,67), 'D3':(40,67), 'R6':(45,67), 'C3':(50,67),
 'R7':(35,71), 'D4':(40,71), 'R8':(45,71), 'C4':(50,71),
 'R9':(35,80), 'D5':(40,80), 'R10':(45,80),
 'R33':(35,84), 'D7':(40,84), 'R34':(45,84),
 'R35':(35,88), 'D8':(40,88), 'R36':(45,88),
 'R37':(35,92), 'D9':(40,92), 'R38':(45,92),
 'J1':(26,59),
 'R13':(53,49), 'C5':(57,49), 'C8':(61,49), 'C9':(65,49),
 'C13':(52,74), 'C11':(57,74), 'C10':(62,74), 'C7':(67,74),
 'C14':(53,78), 'C12':(53,82), 'C15':(57,78), 'C6':(64,80),
 'C19':(53,86), 'C20':(57,86),
 'R20':(71,59), 'R21':(71,65), 'R22':(71,69),
 'C33':(56,90), 'C35':(66,90), 'C36':(70,90),
 'U4':(61,93), 'C34':(61,98),
 'J7':(88.54,63.5), 'J4':(88.54,92), 'J2':(86,101),
 'R43':(83,88), 'R44':(83,92), 'C40':(83,96),
 'C24':(80,66), 'C25':(80,70),
}

affected = set()
for fp in board.GetFootprints():
 ref = fp.GetReference()
 if ref in targets:
  x,y = targets[ref]
  target = pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
  if fp.GetPosition() != target:
   affected.update(p.GetNetCode() for p in fp.Pads() if p.GetNetCode())
   fp.SetPosition(target)
if not any(f.GetReference()=='MH4' for f in board.GetFootprints()):
 fp=pcbnew.FootprintLoad(str(base/'hardware/EEG_Footprints.pretty'),'MountingHole_3.2mm_M3')
 fp.SetReference('MH4');fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(96),pcbnew.FromMM(96)));fp.SetBoardOnly(True);fp.SetExcludedFromBOM(True);fp.SetExcludedFromPosFiles(True);board.Add(fp)
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
