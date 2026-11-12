"""Run after build_environment.py in FreeCAD. Native editable PartDesign features."""
from pathlib import Path
import json
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import MeshPart

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
X0 = CX + " - Parameters.ClampWidth / 2"
Y0 = "-Parameters.BeamClearance - Parameters.ClampWall"
ZLOW = "-Parameters.BeamHeight - Parameters.PlateThickness - Parameters.BeamClearance - Parameters.ClampShelf"
TOP = "Parameters.BeamClearance"
DEPTH = "Parameters.BeamWidth + 2 * Parameters.BeamClearance + Parameters.ClampWall"
primitive("AdditiveBox", "ClampBottom", "Обхват — нижняя полка", {
    "Length":"Parameters.ClampWidth", "Width":DEPTH, "Height":"Parameters.ClampShelf"}, (X0,Y0,ZLOW))
primitive("AdditiveBox", "ClampSpine", "Обхват — наружная стенка", {
    "Length":"Parameters.ClampWidth", "Width":"Parameters.ClampWall",
    "Height":"Parameters.BeamHeight + Parameters.PlateThickness + 2 * Parameters.BeamClearance + 2 * Parameters.ClampShelf"}, (X0,Y0,ZLOW))
primitive("AdditiveBox", "ClampTop", "Обхват — верхняя полка", {
    "Length":"Parameters.ClampWidth", "Width":DEPTH, "Height":"Parameters.ClampShelf"}, (X0,Y0,TOP))
primitive("SubtractiveBox", "SpacerNotch", "Прорезь под проставку 66 мм", {
    "Length":"Parameters.SpacerWidth + Parameters.SpacerClearance",
    "Width":"Parameters.BeamWidth + 2 * Parameters.BeamClearance + 1 mm", "Height":"Parameters.ClampShelf + 2 mm"},
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

def rail_position(d, t, xexpr=X0):
    # d: away from table towards hinges. t: along upward normal to laptop.
    return (xexpr,
        "Parameters.FrontY - (%s) * cos(Parameters.LaptopAngle) + (%s) * sin(Parameters.LaptopAngle)" % (d,t),
        "Parameters.FrontZ + (%s) * sin(Parameters.LaptopAngle) + (%s) * cos(Parameters.LaptopAngle)" % (d,t))

upper_t = "Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2 + Parameters.RailWall"
lower_t = "-Parameters.Felt - Parameters.LaptopClearance / 2"
primitive("AdditiveBox", "UpperLaptopRail", "Ноутбук — верхний захват до 75 мм, 30°", {
    "Length":"Parameters.ClampWidth", "Width":"Parameters.UpperGrip + 6 mm", "Height":"Parameters.RailWall"},
    rail_position("-6 mm",upper_t),True)
primitive("AdditiveBox", "LaptopFrontStop", "Ноутбук — упор переднего края", {
    "Length":"Parameters.ClampWidth", "Width":"5 mm",
    "Height":"Parameters.LaptopThickness + 2 * Parameters.Felt + Parameters.LaptopClearance + 2 * Parameters.RailWall"},
    rail_position("-7 mm",upper_t),True)
tip = primitive("AdditiveBox", "LowerLaptopRail", "Ноутбук — нижняя опора до 85 мм", {
    "Length":"Parameters.ClampWidth", "Width":"Parameters.LowerGrip + 6 mm", "Height":"Parameters.RailWall"},
    rail_position("-6 mm",lower_t),True)

# Round the four exposed longitudinal edges at the insertion ends.
a = math.radians(v("LaptopAngle"))
ends = []
for i,e in enumerate(tip.Shape.Edges,1):
    if len(e.Vertexes) != 2:
        continue
    p,q = [z.Point for z in e.Vertexes]
    if abs(p.y-q.y)>1e-6 or abs(p.z-q.z)>1e-6 or abs(abs(p.x-q.x)-v("ClampWidth"))>1e-5:
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
felt.Label = "03 Войлок 4 мм — четыре накладки"
for side,cx in (("Left","-Parameters.MountSpacing / 2"),("Right","Parameters.MountSpacing / 2")):
    for which,t,depth in (("Upper","Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2","Parameters.UpperGrip - 3 mm"),
                          ("Lower","-Parameters.LaptopClearance / 2","Parameters.LowerGrip - 3 mm")):
        obj = doc.addObject("Part::Box", "Felt"+side+which)
        obj.Label = "Войлок — "+side+" / "+which
        felt.addObject(obj)
        obj.Placement = App.Placement(App.Vector(),App.Rotation(App.Vector(1,0,0),150))
        obj.setExpression("Placement.Rotation.Angle","180 deg - Parameters.LaptopAngle")
        obj.setExpression("Length","Parameters.ClampWidth - 4 mm")
        obj.setExpression("Width",depth)
        obj.setExpression("Height","Parameters.Felt")
        for axis,expr in zip("xyz",rail_position("1 mm",t,cx+" - Parameters.ClampWidth / 2 + 2 mm")):
            obj.setExpression("Placement.Base."+axis,expr)
        obj.ViewObject.ShapeColor = (.40,.36,.29)

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

(ROOT / "exports").mkdir(exist_ok=True)
(ROOT / "previews").mkdir(exist_ok=True)
for name,obj in (("holder_left",body),("holder_right",right),("clamp_fit_sample",sample)):
    sh = obj.Shape.copy()
    # Put an outer side of the U profiles on the bed, away from felt contact faces.
    sh.rotate(App.Vector(),App.Vector(0,1,0),90)
    bb = sh.BoundBox
    sh.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    mesh = MeshPart.meshFromShape(Shape=sh,LinearDeflection=.08,AngularDeflection=.12,Relative=False)
    mesh.write(str(ROOT / "exports" / (name+".stl")))
    sh.exportStep(str(ROOT / "exports" / (name+".step")))
    bb=sh.BoundBox
    dims=[bb.XLength,bb.YLength,bb.ZLength]
    if any(z>225 for z in dims[:2]) or dims[2]>265:
        raise RuntimeError("Print envelope exceeds Neptune 4 Pro: "+name)
    if not mesh.isSolid():
        raise RuntimeError("Non-watertight STL: "+name)
    report["geometry"]["left" if name=="holder_left" else "right" if name=="holder_right" else "clamp_sample"]["print_bounds_mm"] = dims
    report["geometry"]["left" if name=="holder_left" else "right" if name=="holder_right" else "clamp_sample"]["mesh_solid"] = True
report["laptop_channel_mm"] = v("LaptopThickness")+2*v("Felt")+v("LaptopClearance")
report["vent_clearance_along_laptop_mm"] = v("VentStart")-v("LowerGrip")
(ROOT / "validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
doc.recompute()
doc.save()
Gui.activeDocument().activeView().saveImage(str(ROOT / "previews" / "assembly.png"),1600,1100,"Current")
print(json.dumps(report,ensure_ascii=False,indent=2))
print("Saved:",doc.FileName)
