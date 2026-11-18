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
H.set(H.getCellFromAlias("StopWidth"),"=CornerX - ClampX")
H.set("C" + H.getCellFromAlias("StopWidth")[1:],"Левый и правый края совпадают с краями основания")
H.set(H.getCellFromAlias("StopThickness"),"=BossDepth")
H.set("C" + H.getCellFromAlias("StopThickness")[1:],"Передняя грань со стороны ноутбука совпадает с передней гранью основания")
H.set("C" + H.getCellFromAlias("StopCapZ")[1:],"Радиус верха равен половине ширины ограничителя")
doc.HookStopCap.Label = "Полукруглый верх ограничителя"
# Right edge flush with the tabletop, with the cable ring removed from the feature chain.
cell = H.getCellFromAlias("StopCenterX")
if not cell:
    row = max(i for i in range(1,250) if H.getContents("A%d" % i)) + 1
    cell = "B%d" % row
    H.set("A%d" % row,"Центр ограничителя X")
    H.setAlias(cell,"StopCenterX")
H.set(cell,"=CornerX - StopWidth / 2")
H.set("C" + cell[1:],"Правый край ограничителя совпадает с правым торцом столешницы")
doc.HookStopStem.setExpression("Placement.Base.x","HookParameters.StopCenterX - HookParameters.StopWidth / 2")
doc.HookStopCap.setExpression("Placement.Base.x","HookParameters.StopCenterX")
doc.HookInsertPocket.BaseFeature = doc.HookStopRim
for name in ("HookEyeRim","HookEyeBore","HookEyeOuter"):
    if doc.getObject(name):
        doc.removeObject(name)
for alias in ("EyeWall","EyeRadius","EyeOverlap","EyeCenterY","EyeCenterZ","EyeThickness","CableEyeWidth","CableEyeFactor","JackDiameter"):
    cell = H.getCellFromAlias(alias)
    if cell:
        H.setAlias(cell,"")
        for col in "ABC":
            H.clear(col + cell[1:])
upper.Label = "Верхний ограничитель — PETG"
doc.recompute()
# Rebind the native finishing edges after the upright moves into the shelf's end plane.
cap_edges = ["Edge%d" % i for i,e in enumerate(doc.HookStopCap.Shape.Edges,1)
             if isinstance(e.Curve,Part.Circle) and abs(e.Curve.Radius-H.StopWidth.Value/2)<1e-5
             and e.BoundBox.ZMin>=H.StopCapZ.Value-1e-5]
if len(cap_edges)!=2:
    raise RuntimeError("Unable to identify rounded stop rim edges")
doc.HookStopRim.Base = (doc.HookStopCap,cap_edges)
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
report["right_edge_alignment"] = {"tabletop_x_mm":q("CornerX"),"stop_right_x_mm":q("StopCenterX")+q("StopWidth")/2}
outside = Part.makeBox(100,200,200,App.Vector(q("CornerX")+1e-5,-50,-80))
report["material_beyond_right_edge_mm3"] = upper.Shape.common(outside).Volume
assert report["material_beyond_right_edge_mm3"]<1e-5
report["cable_ring"] = {"present":False,"removed_per_user_request":True}
report["base_edge_alignment"] = {"stop_left_x_mm":q("StopCenterX")-q("StopWidth")/2,
                                "base_left_x_mm":q("ClampX"),
                                "stop_front_y_mm":q("FrontY")-q("StopThickness"),
                                "base_front_y_mm":q("BossY")}
assert abs(report["base_edge_alignment"]["stop_left_x_mm"]-q("ClampX"))<1e-6
assert abs(report["base_edge_alignment"]["stop_front_y_mm"]-q("BossY"))<1e-6
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("Updated: 25mm stop rise, lower clamp ends 0.4mm before the corrected leg, hardware moved with clamp.")
