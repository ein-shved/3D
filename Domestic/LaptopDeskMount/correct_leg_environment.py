"""Correct the existing environment only: U frames without lengthwise rails."""
from pathlib import Path
import json
import shutil
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore

ROOT = Path(__file__).resolve().parent
D = App.getDocument("LaptopDeskMount")
backup = ROOT / "archive" / "LaptopDeskMount_before_leg_orientation_fix.FCStd"
if not backup.exists():
    shutil.copy2(D.FileName, backup)
D.openTransaction("Исправить ориентацию профиля ног и удалить лишние связи")
try:
    cell = D.Parameters.getCellFromAlias("LegInset")
    D.Parameters.set(cell, "=BeamHeight / 2")
    D.Parameters.set("C" + cell[1:], "Профиль ноги повёрнут на 90° к перекладине: толщина вдоль X равна высоте перекладины; наружные углы ноги и столешницы совпадают")
    for side, y in (("Near", "0 mm"), ("Far", "Parameters.TableAlong - 2 * Parameters.Overhang - Parameters.BeamWidth")):
        beam = D.getObject("BeamFull" + side)
        beam.setExpression("Length", "Parameters.TableAcross")
        beam.setExpression("Placement.Base.x", "-Parameters.TableAcross / 2")
        beam.setExpression("Placement.Base.y", y)
        for end, x in (("Left", "-Parameters.TableAcross / 2 + Parameters.LegInset - Parameters.BeamHeight / 2"),
                       ("Right", "Parameters.TableAcross / 2 - Parameters.LegInset - Parameters.BeamHeight / 2")):
            leg = D.getObject("Leg" + side + end)
            leg.setExpression("Length", "Parameters.BeamHeight")
            leg.setExpression("Width", "Parameters.BeamWidth")
            leg.setExpression("Placement.Base.x", x)
            leg.setExpression("Placement.Base.y", y)
    for name in ("LongRailLeft", "LongRailRight"):
        if D.getObject(name):
            D.removeObject(name)
    D.recompute()
    # Check the frame profile only. Hook placement is intentionally left for user review.
    for side in ("Near", "Far"):
        beam = D.getObject("BeamFull" + side)
        for end in ("Left", "Right"):
            leg = D.getObject("Leg" + side + end)
            assert leg.Shape.isValid()
            assert abs(leg.Shape.BoundBox.YMin - beam.Shape.BoundBox.YMin) < 1e-6
            assert abs(leg.Shape.BoundBox.YMax - beam.Shape.BoundBox.YMax) < 1e-6
            assert abs(leg.Shape.BoundBox.ZMax - beam.Shape.BoundBox.ZMin) < 1e-6
    D.commitTransaction()
except Exception:
    D.abortTransaction()
    raise

# Present the corrected environment, with the nearby U frame in the foreground.
D.Environment.ViewObject.Visibility = True
D.WholeTable.ViewObject.Visibility = True
for name in ("TableDetail", "Laptop", "PrintedParts", "FeltPads", "FitSamples", "HeadphoneHook"):
    D.getObject(name).ViewObject.Visibility = False
for obj in D.WholeTable.Group:
    obj.ViewObject.Visibility = True
D.TabletopFull.ViewObject.Transparency = 70
v = Gui.activeDocument().activeView()
v.viewAxonometric()
loop = QtCore.QEventLoop()
QtCore.QTimer.singleShot(600, loop.quit)
loop.exec()
v.fitAll()
Gui.updateGui()
v.saveImage(str(ROOT / "previews" / "corrected_leg_environment.png"), 1600, 1100, "Current")
D.save()
(ROOT / "environment_correction.json").write_text(json.dumps({
    "status": "environment_corrected_waiting_user_review",
    "profile": "Beam 60.21Y x30.48Z; leg30.48X x60.21Y, same rectangle bent down90deg",
    "removed": ["LongRailLeft", "LongRailRight"],
    "frame": "Each U frame has one crossbar along the laptop and two vertical ends",
    "hook_changed": False,
    "hook_validation": "previous environment validation superseded; do not use until reviewed"
}, ensure_ascii=False, indent=2) + "\n")
print("Environment corrected and saved; stopped for user review.")
