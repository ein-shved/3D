"""Run after build_environment.py in FreeCAD. Native editable PartDesign features."""
from pathlib import Path
import json
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import MeshPart
import Sketcher

ROOT = Path(__file__).resolve().parent
doc = App.getDocument("LaptopDeskMount")
P = doc.Parameters
if doc.getObject("HolderLeft"):
    raise RuntimeError("Holders already exist; rebuild into a fresh document.")

def v(alias):
    return getattr(P, alias).Value

parts = doc.addObject("App::DocumentObjectGroup", "PrintedParts")
parts.Label = "02 Держатели — PETG, зеркальная пара"
body = doc.addObject("PartDesign::Body", "HolderLeft")
body.Label = "Левый держатель — редактируемая история"
parts.addObject(body)

def primitive(kind, name, label, dims, pos, rotated=False):
    previous = body.Tip
    obj = body.newObject("PartDesign::" + kind, name)
    obj.Label = label
    if rotated:
        obj.Placement = App.Placement(App.Vector(), App.Rotation(App.Vector(1,0,0),150))
        obj.setExpression("Placement.Rotation.Angle", "180 deg - Parameters.LaptopAngle")
    for prop, expr in dims.items():
        obj.setExpression(prop, expr)
    for axis, expr in zip("xyz",pos):
        obj.setExpression("Placement.Base." + axis, expr)
    obj.Refine = True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids) != 1:
        raise RuntimeError("Invalid feature %s: %s" % (name,obj.getStatusString()))
    if previous:
        previous.ViewObject.Visibility = False
    return obj

CX = "-Parameters.MountSpacing / 2"
X0 = CX + " + Parameters.ClampInnerReach - Parameters.ClampWidth"
Y0 = "-Parameters.BeamClearance - Parameters.ClampWall"
ZLOW = "-Parameters.BeamHeight - Parameters.PlateThickness - Parameters.BeamClearance - Parameters.ClampShelf"
TOP = "Parameters.BeamClearance"
DEPTH = "Parameters.BeamWidth + 2 * Parameters.BeamClearance + Parameters.ClampWall"
primitive("AdditiveBox", "ClampBottom", "Обхват — нижняя полка", {
    "Length":"Parameters.ClampWidth", "Width":DEPTH, "Height":"Parameters.ClampShelf"}, (X0,Y0,ZLOW))
primitive("AdditiveBox", "ClampSpine", "Обхват — наружная стенка", {
    "Length":"Parameters.ClampWidth", "Width":"Parameters.ClampWall",
    "Height":"Parameters.BeamHeight + Parameters.PlateThickness + 2 * Parameters.BeamClearance + Parameters.ClampShelf + Parameters.ClampTop"}, (X0,Y0,ZLOW))
primitive("AdditiveBox", "ClampTop", "Обхват — верхняя полка", {
    "Length":"Parameters.ClampWidth", "Width":DEPTH, "Height":"Parameters.ClampTop"}, (X0,Y0,TOP))
primitive("SubtractiveBox", "SpacerNotch", "Прорезь под проставку 66 мм", {
    "Length":"Parameters.SpacerWidth + Parameters.SpacerClearance",
    "Width":"Parameters.BeamWidth + 2 * Parameters.BeamClearance + 1 mm", "Height":"Parameters.ClampTop + 2 mm"},
    (CX+" - (Parameters.SpacerWidth + Parameters.SpacerClearance) / 2", "-Parameters.BeamClearance", "Parameters.BeamClearance - 1 mm"))

# Two capsule-shaped through holes, with every dimension driven by the spreadsheet.
for i, sign in enumerate((-1,1),1):
    cy = "Parameters.BeamWidth / 2 %s Parameters.BoltPitch / 2" % ("-" if sign < 0 else "+")
    for j, end in enumerate((-1,1),1):
        yy = cy + " %s (Parameters.SlotLength - Parameters.SlotWidth) / 2" % ("-" if end < 0 else "+")
        primitive("SubtractiveCylinder", "BoltSlot%dEnd%d" % (i,j), "Отверстие %d — закругление %d" % (i,j),
            {"Radius":"Parameters.SlotWidth / 2", "Height":"Parameters.ClampShelf + 2 mm"},
            (CX,yy,ZLOW+" - 1 mm"))
    clamp = primitive("SubtractiveBox", "BoltSlot%dMiddle" % i,"Отверстие %d — сквозной паз 7.5 × 12" % i,
        {"Length":"Parameters.SlotWidth", "Width":"Parameters.SlotLength - Parameters.SlotWidth", "Height":"Parameters.ClampShelf + 2 mm"},
        (CX+" - Parameters.SlotWidth / 2",cy+" - (Parameters.SlotLength - Parameters.SlotWidth) / 2",ZLOW+" - 1 mm"))

clamp_snapshot = clamp.Shape.copy()
clamp_source = clamp

RAIL_X0 = "-Parameters.LaptopWidth / 2 - Parameters.SideSlack - Parameters.Felt - Parameters.SideWall"
RAIL_WIDTH = "Parameters.ClampWidth"

def rail_position(d, t, xexpr=RAIL_X0):
    # d: away from table towards hinges. t: along upward normal to laptop.
    return (xexpr,
        "Parameters.FrontY - (%s) * cos(Parameters.LaptopAngle) + (%s) * sin(Parameters.LaptopAngle)" % (d,t),
        "Parameters.FrontZ + (%s) * sin(Parameters.LaptopAngle) + (%s) * cos(Parameters.LaptopAngle)" % (d,t))

upper_t = "Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2 + Parameters.RailWall"
lower_t = "-Parameters.Felt - Parameters.LaptopClearance / 2"

# A compact shared back wall joins the U profiles at the same height.
# A constrained YZ sketch fills the space behind the inclined laptop stop,
# inside the existing vertical clamp wall; there is no pendant connector.
back_low = rail_position("-7 mm", lower_t + " - Parameters.RailWall")
back_high = rail_position("-7 mm", upper_t)
points_expr = [(back_low[1],back_low[2]),
               ("-Parameters.BeamClearance",ZLOW),
               ("-Parameters.BeamClearance",back_high[2]),
               (back_high[1],back_high[2])]
previous = body.Tip
sketch = body.newObject("Sketcher::SketchObject", "SharedWallSketch")
sketch.Label = "Общая стенка двух П-профилей — сечение"
sketch.Placement = App.Placement(App.Vector(),App.Rotation(
    App.Vector(0,1,0),App.Vector(0,0,1),App.Vector(1,0,0),"ZXY"))
sketch.setExpression("Placement.Base.x",X0)
points = [App.Vector(body.evalExpression(y).Value,body.evalExpression(z).Value,0) for y,z in points_expr]
for i in range(4):
    sketch.addGeometry(Part.LineSegment(points[i],points[(i+1)%4]),False)
for i in range(4):
    sketch.addConstraint(Sketcher.Constraint("Coincident",i,2,(i+1)%4,1))
    for kind,expr,numeric in (("DistanceX",points_expr[i][0],points[i].x),("DistanceY",points_expr[i][1],points[i].y)):
        index=sketch.addConstraint(Sketcher.Constraint(kind,i,1,numeric))
        sketch.setExpression("Constraints[%d]" % index,expr)
shared = body.newObject("PartDesign::Pad", "SharedBackWall")
shared.Label = "Общая силовая стенка — без нижнего выноса"
shared.Profile = sketch
shared.setExpression("Length","Parameters.ClampWidth")
shared.Refine = True
doc.recompute()
if shared.Shape.isNull() or not shared.Shape.isValid() or len(shared.Shape.Solids)!=1:
    raise RuntimeError("Invalid shared-wall pad: "+shared.getStatusString())
previous.ViewObject.Visibility=False
sketch.ViewObject.Visibility=False

primitive("AdditiveBox", "UpperLaptopRail", "Ноутбук — верхний захват до 75 мм, 30°", {
    "Length":RAIL_WIDTH, "Width":"Parameters.UpperGrip + 6 mm", "Height":"Parameters.RailWall"},
    rail_position("-6 mm",upper_t),True)
primitive("AdditiveBox", "LaptopFrontStop", "Ноутбук — упор переднего края", {
    "Length":RAIL_WIDTH, "Width":"5 mm",
    "Height":"Parameters.LaptopThickness + 2 * Parameters.Felt + Parameters.LaptopClearance + 2 * Parameters.RailWall"},
    rail_position("-7 mm",upper_t),True)
primitive("AdditiveBox", "LowerLaptopRail", "Ноутбук — нижняя опора до 85 мм", {
    "Length":RAIL_WIDTH, "Width":"Parameters.LowerGrip + 6 mm", "Height":"Parameters.RailWall"},
    rail_position("-6 mm",lower_t),True)
tip = primitive("AdditiveBox", "OuterLaptopCheek", "Ноутбук — наружная боковая стенка", {
    "Length":"Parameters.SideWall", "Width":"Parameters.UpperGrip + 4 mm",
    "Height":"Parameters.LaptopThickness + 2 * Parameters.Felt + Parameters.LaptopClearance + 2 * Parameters.RailWall"},
    rail_position("-6 mm",upper_t),True)

# Round the four exposed longitudinal edges at the insertion ends.
a = math.radians(v("LaptopAngle"))
ends = []
for i,e in enumerate(tip.Shape.Edges,1):
    if len(e.Vertexes) != 2:
        continue
    p,q = [z.Point for z in e.Vertexes]
    if abs(p.y-q.y)>1e-6 or abs(p.z-q.z)>1e-6 or abs(abs(p.x-q.x)-doc.UpperLaptopRail.Length.Value)>1e-5:
        continue
    depth = -(p.y-v("FrontY"))*math.cos(a)+(p.z-v("FrontZ"))*math.sin(a)
    if min(abs(depth-v("UpperGrip")),abs(depth-v("LowerGrip")))<1e-5:
        ends.append("Edge%d" % i)
if len(ends) != 4:
    raise RuntimeError("Expected four insertion edges, got %s" % ends)
finish = body.newObject("PartDesign::Fillet", "InsertionFillets")
finish.Label = "Скругления входа R1.2"
finish.Base = (tip,ends)
finish.Radius = 1.2
finish.Refine = True
doc.recompute()
if finish.Shape.isNull() or not finish.Shape.isValid() or len(finish.Shape.Solids)!=1:
    raise RuntimeError("Insertion fillets failed")
tip.ViewObject.Visibility = False
body.Tip = finish
body.ViewObject.ShapeColor = (.94,.47,.13)
finish.ViewObject.ShapeColor = (.94,.47,.13)
finish.ViewObject.LineColor = (.27,.15,.07)

right = doc.addObject("Part::Mirroring", "HolderRight")
right.Label = "Правый держатель — зеркало левого"
parts.addObject(right)
right.Source = body
right.Normal = App.Vector(1,0,0)
right.Base = App.Vector(0,0,0)
right.ViewObject.ShapeColor = (.18,.63,.76)
right.ViewObject.LineColor = (.05,.20,.26)
body.ViewObject.Visibility = True
finish.ViewObject.Visibility = True

felt = doc.addObject("App::DocumentObjectGroup", "FeltPads")
felt.Label = "03 Фетр со скотчем — шесть накладок"
for side,cx in (("Left","-Parameters.MountSpacing / 2"),("Right","Parameters.MountSpacing / 2")):
    for which,t,depth in (("Upper","Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2","Parameters.UpperGrip - 3 mm"),
                          ("Lower","-Parameters.LaptopClearance / 2","Parameters.LowerGrip - 3 mm")):
        obj = doc.addObject("Part::Box", "Felt"+side+which)
        obj.Label = "Фетр со скотчем — "+side+" / "+which
        felt.addObject(obj)
        obj.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),150))
        obj.setExpression("Placement.Rotation.Angle","180 deg - Parameters.LaptopAngle")
        pad_length = RAIL_WIDTH + " - Parameters.SideWall - 2 mm"
        obj.setExpression("Length",pad_length)
        obj.setExpression("Width",depth)
        obj.setExpression("Height","Parameters.Felt")
        pad_x = RAIL_X0 + " + Parameters.SideWall" if side=="Left" else cx+" - Parameters.ClampInnerReach + 2 mm"
        for axis,expr in zip("xyz",rail_position("1 mm",t,pad_x)):
            obj.setExpression("Placement.Base."+axis,expr)
        obj.ViewObject.ShapeColor = (.40,.36,.29)
    side_pad=doc.addObject("Part::Box","Felt"+side+"Side")
    side_pad.Label="Фетр со скотчем — "+side+" / боковая стенка"
    felt.addObject(side_pad)
    side_pad.Placement=App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),150))
    side_pad.setExpression("Placement.Rotation.Angle","180 deg - Parameters.LaptopAngle")
    side_pad.setExpression("Length","Parameters.Felt")
    side_pad.setExpression("Width","Parameters.UpperGrip - 3 mm")
    side_pad.setExpression("Height","Parameters.LaptopThickness")
    sx="-Parameters.LaptopWidth / 2 - Parameters.SideSlack - Parameters.Felt" if side=="Left" else "Parameters.LaptopWidth / 2 + Parameters.SideSlack"
    for axis,expr in zip("xyz",rail_position("1 mm","Parameters.LaptopThickness",sx)):
        side_pad.setExpression("Placement.Base."+axis,expr)
    side_pad.ViewObject.ShapeColor=(.40,.36,.29)

coupons = doc.addObject("App::DocumentObjectGroup", "FitSamples")
coupons.Label = "04 Пробник — только обхват стола"
sample = doc.addObject("PartDesign::SubShapeBinder", "ClampFitSample")
sample.Label = "Пробник посадки, прорези и двух болтов"
coupons.addObject(sample)
sample.Support = [(clamp_source,[""])]
sample.ViewObject.ShapeColor = (.75,.72,.25)
doc.recompute()
if sample.Shape.isNull():
    raise RuntimeError("Empty clamp sample")
sample.ViewObject.Visibility = False
coupons.ViewObject.Visibility = False

doc.recompute()
# Mirroring may hide its source; show both printable bodies in assembly.
body.ViewObject.Visibility = True
finish.ViewObject.Visibility = True

report = {"status":"prototype_requires_fit_sample", "geometry":{},"collisions_mm3":{},"notes":[
    "No structural FEA or physical load test was performed.",
    "Existing screw length and M6 thread are unverified. Clamp adds 4.4 mm below the steel plate including clearance.",
    "Plate outline and bolt positions are provisional; print the clamp sample first.",
    "Full table dimensions, laptop depth and screen geometry are illustrative.",
    "STL and STEP are snapshots. Re-export after changing native parameters."
]}
objects = [("left",body), ("right",right),("clamp_sample",sample)]
for label,obj in objects:
    sh = obj.Shape
    if not sh.isValid() or len(sh.Solids)!=1:
        raise RuntimeError("Not a valid single solid: "+label)
    report["geometry"][label] = {"valid":sh.isValid(),"solids":len(sh.Solids),"volume_mm3":sh.Volume,
                                  "assembly_bounds_mm":[sh.BoundBox.XLength,sh.BoundBox.YLength,sh.BoundBox.ZLength]}

obstacles = [doc.Beam,doc.SpacerLeft,doc.SpacerRight,doc.PlateLeft,doc.PlateRight,doc.TabletopDetail,doc.LaptopBase]
for h in (body,right):
    for obstacle in obstacles:
        overlap = h.Shape.common(obstacle.Shape).Volume
        report["collisions_mm3"][h.Name+" / "+obstacle.Name] = overlap
        if overlap>1e-5:
            raise RuntimeError("Collision: %s / %s: %g mm3" % (h.Name,obstacle.Name,overlap))
for pad in felt.Group:
    for obj in (body,right,doc.LaptopBase):
        overlap = pad.Shape.common(obj.Shape).Volume
        report["collisions_mm3"][pad.Name+" / "+obj.Name] = overlap
        if overlap>1e-5:
            raise RuntimeError("Felt collision: %s / %s" % (pad.Name,obj.Name))

# Verify parameter propagation, then restore the actual lining value/formula.
felt_cell = P.getCellFromAlias("Felt")
original_felt_contents = P.getContents(felt_cell)
original_felt_mm = v("Felt")
test_felt_mm = max(0.1, original_felt_mm - 0.2)
original_volume = body.Shape.Volume
try:
    P.set(felt_cell,"%.9g mm" % test_felt_mm)
    doc.recompute()
    if "_refresh_native_finishing" in globals():
        _refresh_native_finishing()
    if not body.Shape.isValid() or not right.Shape.isValid() or abs(body.Shape.Volume-original_volume)<1:
        raise RuntimeError("Native felt parameter failed to update the holders")
finally:
    P.set(felt_cell,original_felt_contents)
    doc.recompute()
    if "_refresh_native_finishing" in globals():
        _refresh_native_finishing()
if abs(body.Shape.Volume-original_volume)>1e-4:
    raise RuntimeError("Original felt geometry was not restored")
for h in (body,right):
    for name in ("BoltLeft1","BoltLeft2","BoltRight1","BoltRight2","HeadLeft1","HeadLeft2","HeadRight1","HeadRight2"):
        if h.Shape.common(doc.getObject(name).Shape).Volume>1e-5:
            raise RuntimeError("Fastener interference: "+h.Name+" / "+name)
invalid = [(o.Name,o.getStatusString()) for o in doc.Objects if "Invalid" in o.State]
if invalid:
    raise RuntimeError("Document contains invalid objects: "+str(invalid))
report["native_parameter_update_checked"] = "Felt: %.9g -> %.9g -> %.9g mm; both solids valid, original geometry restored" % (original_felt_mm,test_felt_mm,original_felt_mm)
report["assumed_fasteners_clear_holders"] = True
report["invalid_document_objects"] = invalid

# The outboard side is the bed face. The clamp, shared wall, rails and
# laptop cheek must start on the same X plane before rotating for export.
bed_x = doc.OuterLaptopCheek.Placement.Base.x
for feature in (doc.ClampBottom,doc.ClampSpine,doc.ClampTop,doc.SharedWallSketch,
                doc.UpperLaptopRail,doc.LaptopFrontStop,doc.LowerLaptopRail):
    if abs(feature.Placement.Base.x-bed_x)>1e-7:
        raise RuntimeError("Step in print bed face: "+feature.Name)
report["common_outboard_print_plane_verified"] = True
report["left_print_plane_x_mm"] = bed_x
report["right_print_plane_x_mm"] = -bed_x

(ROOT / "exports").mkdir(exist_ok=True)
(ROOT / "previews").mkdir(exist_ok=True)
for name,obj in (("holder_left",body),("holder_right",right),("clamp_fit_sample",sample)):
    sh = obj.Shape.copy()
    # Put an outer side of the U profiles on the bed, away from felt contact faces.
    # Left and right need opposite rotations to put the OUTBOARD cheek
    # on Z=0; using +90 for both would print the left cheek as a roof.
    sh.rotate(App.Vector(),App.Vector(0,1,0),90 if name=="holder_right" else -90)
    bb = sh.BoundBox
    sh.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    mesh = MeshPart.meshFromShape(Shape=sh,LinearDeflection=.08,AngularDeflection=.12,Relative=False)
    mesh.write(str(ROOT / "exports" / (name+".stl")))
    sh.exportStep(str(ROOT / "exports" / (name+".step")))
    bb=sh.BoundBox
    dims=[bb.XLength,bb.YLength,bb.ZLength]
    bed_faces=[f for f in sh.Faces if all(abs(vertex.Point.z)<1e-6 for vertex in f.Vertexes)]
    if not bed_faces:
        raise RuntimeError("No planar bed contact: "+name)
    if any(z>225 for z in dims[:2]) or dims[2]>265:
        raise RuntimeError("Print envelope exceeds Neptune 4 Pro: "+name)
    if not mesh.isSolid():
        raise RuntimeError("Non-watertight STL: "+name)
    report["geometry"]["left" if name=="holder_left" else "right" if name=="holder_right" else "clamp_sample"]["print_bounds_mm"] = dims
    report["geometry"]["left" if name=="holder_left" else "right" if name=="holder_right" else "clamp_sample"]["mesh_solid"] = True
    report["geometry"]["left" if name=="holder_left" else "right" if name=="holder_right" else "clamp_sample"]["bed_contact_area_mm2"] = sum(f.Area for f in bed_faces)
report["laptop_channel_mm"] = v("LaptopThickness")+2*v("Felt")+v("LaptopClearance")
report["lining_thickness_mm"] = v("Felt")
report["laptop_wall_thickness_mm"] = v("RailWall")
report["outboard_cheek_thickness_mm"] = v("SideWall")
report["vent_clearance_along_laptop_mm"] = v("VentStart")-v("LowerGrip")
report["revision"] = "Compact shared wall, reinforced clamp, outboard cheek and clamp aligned to a single flat print bed face"
report["clamp_wall_mm"] = v("ClampWall")
report["clamp_top_mm"] = v("ClampTop")
report["clamp_under_bolts_mm"] = v("ClampShelf")
report["top_to_tabletop_clearance_mm"] = v("SpacerHeight")-v("BeamClearance")-v("ClampTop")
report["side_clearance_after_felt_mm_per_side"] = v("SideSlack")
(ROOT / "validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
view_macro = ROOT / "view_detail.FCMacro"
exec(compile(view_macro.read_text(),str(view_macro),"exec"),{"__file__":str(view_macro)})
doc.recompute()
doc.save()
Gui.activeDocument().activeView().saveImage(str(ROOT / "previews" / "assembly.png"),1600,1100,"Current")
print(json.dumps(report,ensure_ascii=False,indent=2))
print("Saved:",doc.FileName)
