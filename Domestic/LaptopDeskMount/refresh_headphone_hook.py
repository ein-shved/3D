"""Apply corrected U-frame fit and the user's 30mm rounded rectangle in place."""
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
p = ROOT / "refine_headphone_details.py"
details = {"__file__":str(p),"__name__":"hook_details"}
exec(compile(p.read_text(),str(p),"exec"),details)
guide_placements = details["capture_guides"](doc)
details["set_dimensions"](doc)
p = ROOT / "flatten_headphone_hook.py"
module = {"__file__":str(p),"__name__":"hook_flat_base"}
exec(compile(p.read_text(),str(p),"exec"),module)
module["apply_flat_base"](doc)
details["round_joint"](doc)

H.set(H.getCellFromAlias("LowerOffset"), "=ProfileHeight")
H.set("C" + H.getCellFromAlias("LowerOffset")[1:],
      "Толщина ноги вдоль перекладины после поворота профиля: 30.48 мм; обхват заканчивается перед внутренней гранью ноги")
H.set(H.getCellFromAlias("StopRise"), "30 mm")
H.set("C" + H.getCellFromAlias("StopRise")[1:], "Задано пользователем: выступ 30 мм над поверхностью столешницы")
H.set("C" + H.getCellFromAlias("CornerLegInset")[1:], "Половина толщины ноги вдоль X: BeamHeight / 2 = 15.24 мм")
H.set(H.getCellFromAlias("StopWidth"),"=CornerX - ClampX")
H.set("C" + H.getCellFromAlias("StopWidth")[1:],"Левый и правый края совпадают с краями основания")
H.set(H.getCellFromAlias("StopThickness"),"=BossDepth")
H.set("C" + H.getCellFromAlias("StopThickness")[1:],"Передняя грань со стороны ноутбука совпадает с передней гранью основания")
# Right edge stays flush with the tabletop; the current oval loop is rebuilt below.
cell = H.getCellFromAlias("StopCenterX")
if not cell:
    row = max(i for i in range(1,250) if H.getContents("A%d" % i)) + 1
    cell = "B%d" % row
    H.set("A%d" % row,"Центр ограничителя X")
    H.setAlias(cell,"StopCenterX")
H.set(cell,"=CornerX - StopWidth / 2")
H.set("C" + cell[1:],"Правый край ограничителя совпадает с правым торцом столешницы")
doc.HookStopStem.setExpression("Placement.Base.x","HookParameters.StopCenterX - HookParameters.StopWidth / 2")
doc.HookStopStem.setExpression("Height","HookParameters.StopTop - HookParameters.ShelfBottom")
doc.HookInsertPocket.BaseFeature = doc.HookStopRim
for name in ("HookEyeRim","HookEyeBore","HookEyeOuter"):
    if doc.getObject(name):
        doc.removeObject(name)
for alias in ("EyeWall","EyeRadius","EyeOverlap","EyeCenterY","EyeCenterZ","EyeThickness","CableEyeWidth","CableEyeFactor"):
    cell = H.getCellFromAlias(alias)
    if cell:
        H.setAlias(cell,"")
        for col in "ABC":
            H.clear(col + cell[1:])
upper.Label = "Верхний ограничитель — PETG"
doc.recompute()
# Replace the former semicircle with a flat top and two rounded corners.
cell = H.getCellFromAlias("StopCornerRadius")
if not cell:
    row = max(i for i in range(1,250) if H.getContents("A%d" % i)) + 1
    cell = "B%d" % row
    H.set("A%d" % row,"Скругление верхних углов")
    H.setAlias(cell,"StopCornerRadius")
H.set(cell,"10 mm")
H.set("C" + cell[1:],"Прямоугольный силуэт с двумя верхними углами R10")
H.set("C" + H.getCellFromAlias("StopTop")[1:],"Плоский верх смягчённого прямоугольника")
doc.recompute()
corner_edges = ["Edge%d" % i for i,e in enumerate(doc.HookStopStem.Shape.Edges,1)
                if abs(e.BoundBox.ZMin-H.StopTop.Value)<1e-5 and e.BoundBox.ZLength<1e-6
                and e.BoundBox.XLength<1e-6 and abs(e.BoundBox.YLength-H.StopThickness.Value)<1e-5]
if len(corner_edges)!=2:
    raise RuntimeError("Unable to identify the two upper rectangle corners")
corners = doc.getObject("HookStopCorners")
if corners is None:
    corners = upper.newObject("PartDesign::Fillet","HookStopCorners")
corners.Label = "Верхние углы прямоугольного ограничителя R10"
corners.Base = (doc.HookStopStem,corner_edges)
corners.BaseFeature = doc.HookStopStem
corners.setExpression("Radius","HookParameters.StopCornerRadius")
corners.Refine = True
doc.recompute()
if not corners.Shape.isValid():
    raise RuntimeError("Invalid rounded rectangle corners")
rim_edges = []
for i,e in enumerate(corners.Shape.Edges,1):
    bb=e.BoundBox
    if bb.YLength<1e-6 and bb.ZMin>=H.StopTop.Value-H.StopCornerRadius.Value-1e-5:
        if isinstance(e.Curve,Part.Circle) or (bb.ZLength<1e-6 and abs(bb.ZMax-H.StopTop.Value)<1e-5):
            rim_edges.append("Edge%d" % i)
if len(rim_edges)!=6:
    raise RuntimeError("Unable to identify rectangle rim: " + str(rim_edges))
doc.HookStopRim.Base = (corners,rim_edges)
doc.HookStopRim.BaseFeature = corners
doc.HookStopRim.setExpression("Radius","HookParameters.StopEdgeRadius")
doc.HookStopRim.Label = "Мягкие кромки прямоугольного верха R2.5"
if doc.getObject("HookStopCap"):
    doc.removeObject("HookStopCap")
cell = H.getCellFromAlias("StopCapZ")
if cell:
    H.setAlias(cell,"")
    for col in "ABC": H.clear(col+cell[1:])
order=[o for o in upper.Group if o!=corners]
order.insert(order.index(doc.HookStopRim),corners)
upper.Group=order
upper.Tip=doc.HookInsertLeadIn
details["add_oval_loop"](doc)
p = ROOT / "finish_headphone_walls.py"
walls={"__file__":str(p),"__name__":"hook_walls"}
exec(compile(p.read_text(),str(p),"exec"),walls)
walls["finish_lower"](doc)
details["rebind_user_guides"](doc,guide_placements)
walls["finish_insert_pair"](doc)
upper.Label="Верхний ограничитель с овальной петлёй — PETG"
lower.Label="Нижний захват — PETG, M4×15"
for o in upper.Group:
    o.ViewObject.Visibility = o==upper.Tip
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
doc.HookInsertReference.Shape = Part.makeCylinder(q("InsertOuterDiameter")/2, q("InsertLength"), App.Vector(x,y,q("UpperBossBottom"))).cut(
    Part.makeCylinder(2, q("InsertLength"), App.Vector(x,y,q("UpperBossBottom"))))
doc.HookBoltReference.Shape = Part.makeCylinder(q("HeadDiameter")/2, q("HeadHeight"), App.Vector(x,y,q("HeadSeatZ")-q("HeadHeight"))).fuse(
    Part.makeCylinder(2, q("BoltLength"), App.Vector(x,y,q("HeadSeatZ"))))
doc.HookInsertReference.Label="Термовставка M4, Ø5.69 × 6 — условная геометрия"
doc.HookBoltReference.Label="Болт M4×15, головка Ø7 — условная геометрия"
doc.HookHardware.Label="Крепёж — M4×15, вставка M4 Ø5.69 × 6"
doc.recompute()
# Reuse the full final-position validation, retaining the installed laptop mount checks.
source = (ROOT / "build_headphone_hook.py").read_text()
tail = source[source.index('report = {"status":'):]
exec(compile(tail, str(ROOT / "build_headphone_hook.py"), "exec"), globals())
report["stop_height_mm"] = q("StopRise")
report["stop_profile"] = {"shape":"rounded_rectangle","corner_radius_mm":q("StopCornerRadius"),"rim_radius_mm":doc.HookStopRim.Radius.Value,"flat_top_width_mm":q("StopWidth")-2*q("StopCornerRadius")}
report["leg_thickness_along_beam_mm"] = q("LowerOffset")
report["clearance_to_leg_mm"] = doc.LegNearRight.Shape.BoundBox.XMin - lower.Shape.BoundBox.XMax
assert abs(report["clearance_to_leg_mm"] - q("FitClearance")) < 1e-6
assert abs(q("StopTop") - q("TableTopZ") - 30) < 1e-6
report["environment_version"] = "User approved U frames: legs30.48X x60.21Y, no longitudinal rails"
report["right_edge_alignment"] = {"tabletop_x_mm":q("CornerX"),"stop_right_x_mm":q("StopCenterX")+q("StopWidth")/2}
outside = Part.makeBox(100,200,200,App.Vector(q("CornerX")+1e-5,-50,-80))
report["material_beyond_right_edge_mm3"] = upper.Shape.common(outside).Volume
assert report["material_beyond_right_edge_mm3"]<1e-5
report["cable_ring"] = {"present":True,"shape":"vertical_oval_loop","passage_mm":q("CableGap"),"wall_mm":q("CableWall"),"top_z_mm":q("CableTop")}
report["equal_rear_joint"]={"upper_mm":q("ShelfTop")-q("ChannelRoof"),"opening_mm":q("ChannelRoof")-q("RearLipTop"),"lower_mm":q("RearLipTop")-q("ShelfBottom"),"inner_radius_mm":q("JointInsideRadius"),"tongue_thickness_mm":q("TongueTop")-q("TongueBottom")}
report["wall_finishing"]={"merged_sidewalls":True,"upper_bottom_radius_mm":q("BottomEdgeRadius"),"lower_side_radius_mm":q("LowerSideRadius"),"entry_radius_mm":q("EntryCornerRadius"),"deep_back_rounds_rolled_back":doc.getObject("HookChannelInnerRounds") is None and doc.getObject("HookTongueRounds") is None}
report["bolt"]["material_under_head_mm"]=q("LowerBossTop")-q("HeadSeatZ")
zmin = upper.Shape.BoundBox.ZMin
base_area = sum(f.Area for f in upper.Shape.Faces if f.BoundBox.ZLength<1e-5 and abs(f.BoundBox.ZMin-zmin)<1e-5)
report["flat_print_base"] = {"z_mm":zmin,"nominal_z_mm":q("ShelfBottom"),"contact_area_mm2":base_area,
                            "shelf_width_mm":q("StopWidth"),"shelf_depth_mm":q("UpperBackEnd")-q("BossY"),
                            "front_projection_removed":doc.getObject("HookFrontBoss") is None}
assert abs(zmin-q("ShelfBottom"))<1e-5
assert base_area>4000
report["bolt"]["head_pocket_depth_mm"]=q("HeadPocketDepth")
report["bolt"]["upper_insert_bottom_z_mm"]=q("UpperBossBottom")
report["base_edge_alignment"] = {"stop_left_x_mm":q("StopCenterX")-q("StopWidth")/2,
                                "base_left_x_mm":q("ClampX"),
                                "stop_front_y_mm":q("FrontY")-q("StopThickness"),
                                "base_front_y_mm":q("BossY")}
assert abs(report["base_edge_alignment"]["stop_left_x_mm"]-q("ClampX"))<1e-6
assert abs(report["base_edge_alignment"]["stop_front_y_mm"]-q("BossY"))<1e-6
(ROOT / "headphone_hook_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("Updated: 30mm rounded-rectangle stop rise, lower clamp ends 0.4mm before the corrected leg, hardware moved with clamp.")
