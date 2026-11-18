"""Apply corrected U-frame fit and the user's 25mm stop height in place."""
from pathlib import Path
import json
import shutil
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parent
doc = App.getDocument("LaptopDeskMount")
H = doc.HookParameters
upper, lower = doc.HeadphoneHookUpper, doc.HeadphoneHookLower
backup = ROOT / "archive" / "LaptopDeskMount_before_hook_25mm_and_leg_fit.FCStd"
if not backup.exists():
    shutil.copy2(doc.FileName, backup)
original_holders = {name: doc.getObject(name).Shape.copy() for name in ("HolderLeft", "HolderRight")}

H.set(H.getCellFromAlias("LowerOffset"), "=ProfileHeight")
H.set("C" + H.getCellFromAlias("LowerOffset")[1:],
      "Толщина ноги вдоль перекладины после поворота профиля: 30.48 мм; обхват заканчивается перед внутренней гранью ноги")
H.set(H.getCellFromAlias("StopRise"), "25 mm")
H.set("C" + H.getCellFromAlias("StopRise")[1:], "Задано пользователем: выступ 25 мм над поверхностью столешницы")
H.set("C" + H.getCellFromAlias("CornerLegInset")[1:], "Половина толщины ноги вдоль X: BeamHeight / 2 = 15.24 мм")
doc.recompute()
for body in (upper, lower):
    if not body.Shape.isValid() or len(body.Shape.Solids) != 1:
        raise RuntimeError("Invalid updated hook body: " + body.Name)
    for feature in body.Group:
        if "Invalid" in feature.State:
            raise RuntimeError("Invalid native hook feature: " + feature.Name)

def q(alias):
    return getattr(H, alias).Value

# The printed geometry is driven by the sheet; reference hardware is regenerated at its new axis.
x, y = q("ClampX") + q("ClipWidth") / 2, q("BoltY")
doc.HookInsertReference.Shape = Part.makeCylinder(3, q("InsertLength"), App.Vector(x,y,q("UpperBossBottom"))).cut(
    Part.makeCylinder(2, q("InsertLength"), App.Vector(x,y,q("UpperBossBottom"))))
doc.HookBoltReference.Shape = Part.makeCylinder(q("HeadDiameter")/2, q("HeadHeight"), App.Vector(x,y,q("HeadSeatZ")-q("HeadHeight"))).fuse(
    Part.makeCylinder(2, q("BoltLength"), App.Vector(x,y,q("HeadSeatZ"))))
doc.recompute()
# Reuse the full final-position validation, retaining the installed laptop mount checks.
source = (ROOT / "build_headphone_hook.py").read_text()
tail = source[source.index('report = {"status":'):]
exec(compile(tail, str(ROOT / "build_headphone_hook.py"), "exec"), globals())
report["stop_height_mm"] = q("StopRise")
report["leg_thickness_along_beam_mm"] = q("LowerOffset")
report["clearance_to_leg_mm"] = doc.LegNearRight.Shape.BoundBox.XMin - lower.Shape.BoundBox.XMax
assert abs(report["clearance_to_leg_mm"] - q("FitClearance")) < 1e-6
assert abs(q("StopTop") - q("TableTopZ") - 25) < 1e-6
report["environment_version"] = "User approved U frames: legs30.48X x60.21Y, no longitudinal rails"
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("Updated: 25mm stop rise, lower clamp ends 0.4mm before the corrected leg, hardware moved with clamp.")
