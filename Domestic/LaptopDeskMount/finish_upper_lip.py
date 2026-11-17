"""Blend the upper lip into the cheek's mouth, following the user's Sketch001."""
from pathlib import Path
import json
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
import MeshPart

ROOT=Path(__file__).resolve().parent
doc=App.getDocument("LaptopDeskMount")
body=doc.HolderLeft
P=doc.Parameters
if doc.getObject("UpperLipBlend"):
    raise RuntimeError("Upper lip is already finished; edit the existing feature.")
before=body.Shape.copy()
probe_before=doc.ClampFitSample.Shape.copy()
previous=body.Tip

# Preserve/reconstruct the user's new reference independently of the driving sketch.
guide=doc.getObject("Sketch001")
if guide is None:
    data=json.loads((ROOT/"references"/"upper_lip_sketch.json").read_text())
    guide=body.newObject("Sketcher::SketchObject","Sketch001")
    guide.Placement=App.Placement(App.Vector(*data["position"]),App.Rotation(*data["quaternion"]))
    for item in data["geometries"]:
        if item["type"]=="LineSegment":
            geom=Part.LineSegment(App.Vector(*item["start"]),App.Vector(*item["end"]))
        else:
            geom=Part.ArcOfCircle(Part.Circle(App.Vector(*item["center"]),App.Vector(0,0,1),item["radius"]),item["first_parameter"],item["last_parameter"])
        index=guide.addGeometry(geom,False)
        guide.addConstraint(Sketcher.Constraint("Block",index))
guide.Label="Эскиз пользователя — внутренний край верхней полки"
body.Tip=previous

def value(expr):
    return body.evalExpression(expr).Value

# Local coordinates match the reference: u = laptop depth + 6 mm,
# v = distance down from the upper outside surface. The analytic radius
# keeps the inside flat, arc and cheek tangent without altering the flat fit.
r="InsertionFillets.Radius"
dd="Parameters.LowerGrip - Parameters.UpperGrip"
dt="Parameters.LaptopThickness + 2 * Parameters.Felt + Parameters.LaptopClearance + Parameters.RailWall"
distance="sqrt((%s)^2 + (%s)^2)"%(dd,dt)
nd="(%s)/(%s)"%(dt,distance)
nt="(%s)/(%s)"%(dd,distance)
radius="((%s) + (%s) * (Parameters.RailWall - (%s))) / (1 + (%s))"%(r,nt,r,nt)
ue="Parameters.UpperGrip - (%s) + 6 mm"%r
vs="(%s) * (1 - (%s))"%(r,nt)
us="Parameters.UpperGrip - (%s) + (%s) * (%s) + 6 mm"%(r,r,nd)
up="(%s) + (%s) * (%s)"%(ue,radius,nd)
vp="Parameters.RailWall - (%s) * (1 + (%s))"%(radius,nt)
points_expr=[(us,vs),(up,vp),(ue,"Parameters.RailWall"),
             ("(%s) - 2 mm"%ue,"Parameters.RailWall"),("(%s) - 2 mm"%ue,vs)]
points=[App.Vector(value(u),value(v),0) for u,v in points_expr]
R=value(radius)
center=App.Vector(value(ue),P.RailWall.Value-R,0)
first=math.atan2(points[1].y-center.y,points[1].x-center.x)
mid=(first+math.pi/2)/2
arc_mid=center+App.Vector(R*math.cos(mid),R*math.sin(mid),0)

profile=body.newObject("Sketcher::SketchObject","UpperLipBlendSketch")
profile.Label="Верхний упор — касательная к стенке и внутренний радиус"
profile.Placement=guide.Placement
profile.setExpression("Placement.Base.x","OuterLaptopCheek.Placement.Base.x + Parameters.SideWall")
upper="Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2 + Parameters.RailWall"
profile.setExpression("Placement.Base.y","Parameters.FrontY + 6 mm * cos(Parameters.LaptopAngle) + (%s) * sin(Parameters.LaptopAngle)"%upper)
profile.setExpression("Placement.Base.z","Parameters.FrontZ - 6 mm * sin(Parameters.LaptopAngle) + (%s) * cos(Parameters.LaptopAngle)"%upper)
profile.addGeometry(Part.LineSegment(points[0],points[1]),False)
profile.addGeometry(Part.Arc(points[1],arc_mid,points[2]),False)
for i in range(2,5):
    profile.addGeometry(Part.LineSegment(points[i],points[(i+1)%5]),False)
for i,pt in enumerate(points):
    profile.addConstraint(Sketcher.Constraint("Coincident",i,2,(i+1)%5,1))
    for kind,expr,numeric in (("DistanceX",points_expr[i][0],pt.x),("DistanceY",points_expr[i][1],pt.y)):
        index=profile.addConstraint(Sketcher.Constraint(kind,i,1,numeric))
        profile.setExpression("Constraints[%d]"%index,expr)
# Arc center shares the endpoint's U coordinate, ensuring horizontal tangency.
index=profile.addConstraint(Sketcher.Constraint("DistanceX",1,3,center.x))
profile.setExpression("Constraints[%d]"%index,ue)
blend=body.newObject("PartDesign::Pad","UpperLipBlend")
blend.Label="Внутренний край верхнего упора — плавный выход к стенке"
blend.Profile=profile
blend.BaseFeature=doc.LowerElbowRound
blend.setExpression("Length","Parameters.ClampWidth - Parameters.SideWall")
blend.Refine=True
doc.recompute()
if blend.Shape.isNull() or not blend.Shape.isValid() or len(blend.Shape.Solids)!=1:
    raise RuntimeError("Invalid upper-lip blend: "+blend.getStatusString())
previous.ViewObject.Visibility=False
profile.ViewObject.Visibility=False
guide.ViewObject.Visibility=False
# Apply the existing rim chamfers AFTER the new lip, so the new arc and
# cheek transition have the same edge treatment as the rest of the model.
base=blend
for name,plane in (("BedRimChamfer",doc.OuterLaptopCheek.Placement.Base.x),
                   ("InnerRimChamfer",doc.UpperLaptopRail.Shape.BoundBox.XMax)):
    feature=doc.getObject(name)
    names=["Edge%d"%i for i,e in enumerate(base.Shape.Edges,1)
           if e.Length>5 and all(abs(v.Point.x-plane)<1e-5 for v in e.Vertexes)]
    feature.Base=(base,names)
    doc.recompute()
    if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids)!=1:
        raise RuntimeError("Invalid chamfer after upper lip: "+name)
    base.ViewObject.Visibility=False
    base=feature
body.Tip=base
# Keep the feature tree in the same order as the actual dependency chain.
members=[obj for obj in body.Group if obj not in (profile,blend)]
index=members.index(doc.BedRimChamfer)
members[index:index]=[profile,blend]
body.Group=members
body.Tip=base
body.ViewObject.Visibility=True
base.ViewObject.Visibility=True
base.ViewObject.ShapeColor=(.94,.47,.13)
base.ViewObject.LineColor=(.27,.15,.07)
doc.HolderRight.ViewObject.Visibility=True
doc.recompute()

# Verify the actual sketch arc, its two tangencies and the mounted fit.
arc=profile.Geometry[1]
line=profile.Geometry[0]
normal=arc.StartPoint-arc.Center
direction=line.EndPoint-line.StartPoint
direction.normalize()
tangent_error=abs(normal.dot(direction))
flat_error=abs(arc.EndPoint.x-arc.Center.x)
if max(tangent_error,flat_error)>1e-7:
    raise RuntimeError("Upper lip tangent is not continuous")
if before.cut(blend.Shape).Volume>1e-5:
    raise RuntimeError("The cosmetic blend unexpectedly removed original material")
removed=before.cut(body.Shape).Volume
if removed>1e-5:
    raise RuntimeError("The reordered chamfers unexpectedly removed original material")
if probe_before.cut(doc.ClampFitSample.Shape).Volume+doc.ClampFitSample.Shape.cut(probe_before).Volume>1e-5:
    raise RuntimeError("The proven mounting interface changed")

report=json.loads((ROOT/"validation.json").read_text())
for holder in (body,doc.HolderRight):
    for obstacle in [doc.Beam,doc.TabletopDetail,doc.SpacerLeft,doc.SpacerRight,doc.PlateLeft,doc.PlateRight,doc.LaptopBase,*doc.FeltPads.Group]:
        overlap=holder.Shape.common(obstacle.Shape).Volume
        if overlap>1e-5:
            raise RuntimeError("Upper lip collision: "+holder.Name+" / "+obstacle.Name)
        report["collisions_mm3"][holder.Name+" / "+obstacle.Name]=overlap

for name,obj,key in (("holder_left",body,"left"),("holder_right",doc.HolderRight,"right")):
    shape=obj.Shape.copy()
    if not shape.isValid() or len(shape.Solids)!=1:
        raise RuntimeError("Invalid mirrored cosmetic result: "+name)
    volume=shape.Volume
    shape.rotate(App.Vector(),App.Vector(0,1,0),90 if key=="right" else -90)
    bb=shape.BoundBox
    shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.06,AngularDeflection=.10,Relative=False)
    if not mesh.isSolid():
        raise RuntimeError("Non-solid upper lip STL")
    mesh.write(str(ROOT/"exports"/(name+".stl")))
    shape.exportStep(str(ROOT/"exports"/(name+".step")))
    bb=shape.BoundBox
    report["geometry"][key].update(valid=True,solids=1,volume_mm3=volume,mesh_solid=True,
        assembly_bounds_mm=[obj.Shape.BoundBox.XLength,obj.Shape.BoundBox.YLength,obj.Shape.BoundBox.ZLength],
        print_bounds_mm=[bb.XLength,bb.YLength,bb.ZLength],
        bed_contact_area_mm2=sum(f.Area for f in shape.Faces if all(abs(v.Point.z)<1e-6 for v in f.Vertexes)))
report["upper_lip_finish"]={"date":"2026-11-17","both_halves":True,"reference_sketch":guide.Name,
    "radius_mm":arc.Radius,"tangent_error_mm":tangent_error,"flat_tangent_error_mm":flat_error,
    "fully_constrained":profile.FullyConstrained,"extent_across_laptop_slot_mm":blend.Length.Value,
    "original_material_preserved":True,"mounting_sample_unchanged":True,
    "final_material_removed_mm3":removed,
    "feature_order":"UpperLipBlend -> BedRimChamfer -> InnerRimChamfer",
    "nominal_plastic_slot_mm":P.LaptopThickness.Value+2*P.Felt.Value+P.LaptopClearance.Value}
report["physical_fit_feedback"]={**report.get("physical_fit_feedback",{}),"date":"2026-11-17","source":"user",
    "report":"One half printed, lined, mounted and tested; user reports perfect fit.",
    "scope":"User-reported fit of one manufactured half; no destructive or controlled load test."}
report["status"]="user_reported_fit_preserved_after_cosmetic_update"
report["styling"]["native_final_feature"]=body.Tip.Name
report["revision"]="Tangent inner upper lip following Sketch001; both mirrored halves"
guide_name=guide.Name
doc.removeObject(guide_name)
doc.recompute()
report["upper_lip_finish"]["reference_sketch_removed"]=True
report["upper_lip_finish"]["reference_snapshot"]="references/upper_lip_sketch.json"
report["invalid_document_objects"]=[(o.Name,o.getStatusString()) for o in doc.Objects if "Invalid" in o.State]
if report["invalid_document_objects"]:
    raise RuntimeError("Document contains invalid features: "+str(report["invalid_document_objects"]))
(ROOT/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
macro=ROOT/"view_detail.FCMacro"
exec(compile(macro.read_text(),str(macro),"exec"),{"__file__":str(macro)})
doc.recompute()
doc.save()
print(json.dumps(report["upper_lip_finish"],ensure_ascii=False,indent=2))
