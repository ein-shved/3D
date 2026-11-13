"""Apply the user's sketched contour and external edge treatment in FreeCAD."""
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
if doc.getObject("UnifiedCheek"):
    raise RuntimeError("Styling already exists; edit its native features instead of adding it twice.")

# Preserve the hand-drawn reference when rebuilding from source files.
if not doc.getObject("Sketch"):
    ref=json.loads((ROOT/"references"/"styling_sketch.json").read_text())
    user=body.newObject("Sketcher::SketchObject","Sketch")
    user.Placement=App.Placement(App.Vector(*ref["position"]),App.Rotation(*ref["quaternion"]))
    for start,end in ref["lines"]:
        user.addGeometry(Part.LineSegment(App.Vector(*start),App.Vector(*end)),False)
else:
    user=doc.Sketch
user.Label="Эскиз пользователя — переходы бокового контура"
user.ViewObject.Visibility=False
body.Tip=doc.InsertionFillets

def yz(d,t):
    return ("Parameters.FrontY - (%s) * cos(Parameters.LaptopAngle) + (%s) * sin(Parameters.LaptopAngle)"%(d,t),
            "Parameters.FrontZ + (%s) * sin(Parameters.LaptopAngle) + (%s) * cos(Parameters.LaptopAngle)"%(d,t))

upper="Parameters.LaptopThickness + Parameters.Felt + Parameters.LaptopClearance / 2 + Parameters.RailWall"
lower="-Parameters.Felt - Parameters.LaptopClearance / 2 - Parameters.RailWall"
back="-Parameters.BeamClearance - Parameters.ClampWall"
top="Parameters.BeamClearance + Parameters.ClampTop"
bottom="-Parameters.BeamHeight - Parameters.PlateThickness - Parameters.BeamClearance - Parameters.ClampShelf"
# Horizontal upper bridge, the diagonal mouth, and lower elbow follow
# the three lines in the user's sketch. The mouth joins the existing R1.2 entries.
upper_join="((%s) - Parameters.FrontZ - (%s) * cos(Parameters.LaptopAngle)) / sin(Parameters.LaptopAngle)"%(top,upper)
# Equal-radius external tangent to the upper and lower insertion rounds.
# Use the actual native fillet radius so the cheek's mouth has G1 joins.
radius="InsertionFillets.Radius"
delta_d="Parameters.LowerGrip - Parameters.UpperGrip"
delta_t="(%s) - (%s) - Parameters.RailWall"%(upper,lower)
center_distance="sqrt((%s)^2 + (%s)^2)"%(delta_d,delta_t)
normal_d="(%s) / (%s)"%(delta_t,center_distance)
normal_t="(%s) / (%s)"%(delta_d,center_distance)
top_tangent=yz("Parameters.UpperGrip - (%s) + (%s) * (%s)"%(radius,radius,normal_d),
               "(%s) - (%s) + (%s) * (%s)"%(upper,radius,radius,normal_t))
bottom_tangent=yz("Parameters.LowerGrip - (%s) + (%s) * (%s)"%(radius,radius,normal_d),
                  "(%s) + Parameters.RailWall - (%s) + (%s) * (%s)"%(lower,radius,radius,normal_t))
points=[(back,top),yz(upper_join,upper),
        yz("Parameters.UpperGrip - (%s)"%radius,upper),
        top_tangent,bottom_tangent,
        yz("Parameters.LowerGrip - (%s)"%radius,lower),
        yz("-7 mm",lower),(back,bottom)]
sk=body.newObject("Sketcher::SketchObject","UnifiedCheekSketch")
sk.Label="Цельный контур щеки по эскизу пользователя"
sk.Placement=doc.SharedWallSketch.Placement
sk.setExpression("Placement.Base.x","OuterLaptopCheek.Placement.Base.x")
vertices=[App.Vector(body.evalExpression(y).Value,body.evalExpression(z).Value,0) for y,z in points]
for i in range(len(vertices)):
    sk.addGeometry(Part.LineSegment(vertices[i],vertices[(i+1)%len(vertices)]),False)
for i,pt in enumerate(vertices):
    sk.addConstraint(Sketcher.Constraint("Coincident",i,2,(i+1)%len(vertices),1))
    for kind,expr,num in (("DistanceX",points[i][0],pt.x),("DistanceY",points[i][1],pt.y)):
        idx=sk.addConstraint(Sketcher.Constraint(kind,i,1,num))
        sk.setExpression("Constraints[%d]"%idx,expr)
pad=body.newObject("PartDesign::Pad","UnifiedCheek")
pad.Label="Цельная боковая стенка — переходы и наклонный торец"
pad.Profile=sk
pad.setExpression("Length","Parameters.SideWall")
pad.Refine=True
doc.recompute()
if pad.Shape.isNull() or not pad.Shape.isValid() or len(pad.Shape.Solids)!=1:
    raise RuntimeError("Invalid unified cheek: "+pad.getStatusString())
doc.InsertionFillets.ViewObject.Visibility=False
sk.ViewObject.Visibility=False
body.Tip=pad
doc.HolderRight.ViewObject.Visibility=True
body.ViewObject.Visibility=True
pad.ViewObject.ShapeColor=(.94,.47,.13)
print("Unified cheek valid; constrained:",sk.FullyConstrained)
print("Vertices:",[(round(v.x,3),round(v.y,3)) for v in vertices])

def blend_pad(name,label,expressions):
    previous=body.Tip
    profile=body.newObject("Sketcher::SketchObject",name+"Sketch")
    profile.Label=label+" — сечение"
    profile.Placement=doc.SharedWallSketch.Placement
    profile.setExpression("Placement.Base.x","OuterLaptopCheek.Placement.Base.x")
    coords=[App.Vector(body.evalExpression(y).Value,body.evalExpression(z).Value,0) for y,z in expressions]
    for i in range(len(coords)):
        profile.addGeometry(Part.LineSegment(coords[i],coords[(i+1)%len(coords)]),False)
    for i,point in enumerate(coords):
        profile.addConstraint(Sketcher.Constraint("Coincident",i,2,(i+1)%len(coords),1))
        for kind,expr,value in (("DistanceX",expressions[i][0],point.x),("DistanceY",expressions[i][1],point.y)):
            index=profile.addConstraint(Sketcher.Constraint(kind,i,1,value))
            profile.setExpression("Constraints[%d]"%index,expr)
    feature=body.newObject("PartDesign::Pad",name)
    feature.Label=label
    feature.Profile=profile
    feature.setExpression("Length","Parameters.ClampWidth")
    feature.Refine=True
    doc.recompute()
    if feature.Shape.isNull() or not feature.Shape.isValid() or len(feature.Shape.Solids)!=1:
        raise RuntimeError("Invalid full-width blend: "+name)
    previous.ViewObject.Visibility=False
    profile.ViewObject.Visibility=False
    return feature

upper_at_back="(Parameters.FrontY + (%s) * sin(Parameters.LaptopAngle) - (%s)) / cos(Parameters.LaptopAngle)"%(upper,back)
upper_base=blend_pad("UpperBaseBlend","Верхний переход обхвата — на всю ширину",
                    [(back,top),yz(upper_join,upper),yz(upper_at_back,upper)])
lower_root=yz("-7 mm",lower)
lower_base=blend_pad("LowerBaseBlend","Нижний переход обхвата — на всю ширину",
                    [lower_root,(back,bottom),(back,lower_root[1])])

def rounded_corner(name,label,y,z,radius,min_length=0):
    previous=body.Tip
    edge_names=[]
    for i,edge in enumerate(previous.Shape.Edges,1):
        if len(edge.Vertexes)!=2 or edge.Length<=min_length:
            continue
        a,b=[v.Point for v in edge.Vertexes]
        if abs(a.y-y)<1e-4 and abs(a.z-z)<1e-4 and abs(a.y-b.y)<1e-6 and abs(a.z-b.z)<1e-6:
            edge_names.append("Edge%d"%i)
    if not edge_names:
        raise RuntimeError("Missing cosmetic corner: "+name)
    obj=body.newObject("PartDesign::Fillet",name)
    obj.Label=label
    obj.Base=(previous,edge_names)
    obj.Radius=radius
    obj.Refine=True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError("Invalid cosmetic fillet: "+name)
    previous.ViewObject.Visibility=False
    return obj

def evaluated(expr):
    return body.evalExpression(expr).Value

rounded_corner("UpperContourRound","Верхний переход боковой стенки R4",vertices[1].x,vertices[1].y,4)
rounded_corner("UpperClampRounds","Наружные торцы верхнего обхвата R2",
               P.BeamWidth.Value+P.BeamClearance.Value,evaluated(top),2)
rounded_corner("LowerClampRound","Наружный торец нижней полки R1.2",
               P.BeamWidth.Value+P.BeamClearance.Value,evaluated(bottom),1.2)
rounded_corner("LowerElbowRound","Нижний наружный переход R1.2",
               evaluated(back),evaluated(bottom),1.2,P.ClampWidth.Value-6)

for name,label,plane in (("BedRimChamfer","Наружные фаски общей плоскости 0.6",doc.OuterLaptopCheek.Placement.Base.x),
                         ("InnerRimChamfer","Фаски свободных внутренних торцов 0.6",doc.UpperLaptopRail.Shape.BoundBox.XMax)):
    previous=body.Tip
    # Long rim edges avoid the tiny tangent fragments at the existing R1.2
    # insertion lips. Tangent rounded sections are handled by OCCT itself.
    names=["Edge%d"%i for i,e in enumerate(previous.Shape.Edges,1)
           if e.Length>5 and all(abs(v.Point.x-plane)<1e-5 for v in e.Vertexes)]
    obj=body.newObject("PartDesign::Chamfer",name)
    obj.Label=label
    obj.Base=(previous,names)
    obj.Size=.6
    obj.Refine=True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError("Invalid cosmetic chamfer: "+name)
    previous.ViewObject.Visibility=False

finish=body.Tip
finish.ViewObject.ShapeColor=(.94,.47,.13)
finish.ViewObject.LineColor=(.27,.15,.07)
user.ViewObject.Visibility=False
doc.recompute()

def _refresh_native_finishing():
    # A dimensional change can invalidate FreeCAD's mapped edge references
    # even when the edge order is unchanged. Resolve our geometric selectors
    # again before validating/exporting the new dimensions.
    # Re-resolve the four original insertion edges as the inner rail faces move.
    raw=doc.OuterLaptopCheek.Shape
    angle=math.radians(P.LaptopAngle.Value)
    names=[]
    for i,edge in enumerate(raw.Edges,1):
        if len(edge.Vertexes)!=2 or abs(edge.Length-P.ClampWidth.Value)>1e-5:
            continue
        a,b=[v.Point for v in edge.Vertexes]
        depth=-(a.y-P.FrontY.Value)*math.cos(angle)+(a.z-P.FrontZ.Value)*math.sin(angle)
        if abs(a.y-b.y)<1e-6 and abs(a.z-b.z)<1e-6 and min(abs(depth-P.UpperGrip.Value),abs(depth-P.LowerGrip.Value))<1e-5:
            names.append("Edge%d"%i)
    if len(names)!=4:
        raise RuntimeError("Cannot resolve insertion edges after changing lining")
    doc.InsertionFillets.Base=(doc.OuterLaptopCheek,names)
    doc.recompute()
    point=doc.UnifiedCheekSketch.Geometry[1].StartPoint
    targets=[("UpperContourRound",point.x,point.y,0),
             ("UpperClampRounds",P.BeamWidth.Value+P.BeamClearance.Value,evaluated(top),0),
             ("LowerClampRound",P.BeamWidth.Value+P.BeamClearance.Value,evaluated(bottom),0),
             ("LowerElbowRound",evaluated(back),evaluated(bottom),P.ClampWidth.Value-6)]
    for name,y,z,min_length in targets:
        obj=doc.getObject(name)
        base=obj.Base[0]
        names=[]
        for i,edge in enumerate(base.Shape.Edges,1):
            if len(edge.Vertexes)==2 and edge.Length>min_length:
                a,b=[v.Point for v in edge.Vertexes]
                if abs(a.y-y)<1e-4 and abs(a.z-z)<1e-4 and abs(a.y-b.y)<1e-6 and abs(a.z-b.z)<1e-6:
                    names.append("Edge%d"%i)
        obj.Base=(base,names)
        doc.recompute()
    for name,plane in (("BedRimChamfer",doc.OuterLaptopCheek.Placement.Base.x),
                       ("InnerRimChamfer",doc.UpperLaptopRail.Shape.BoundBox.XMax)):
        obj=doc.getObject(name)
        base=obj.Base[0]
        names=["Edge%d"%i for i,e in enumerate(base.Shape.Edges,1)
               if e.Length>5 and all(abs(v.Point.x-plane)<1e-5 for v in e.Vertexes)]
        obj.Base=(base,names)
        doc.recompute()

_refresh_native_finishing()

# Reuse the existing assembly, parameter, bed-plane, STL and STEP checks
# without rebuilding the document or replacing the user's sketch.
right=doc.HolderRight
felt=doc.FeltPads
sample=doc.ClampFitSample
def v(alias):
    return getattr(P,alias).Value
source=(ROOT/"build_holders.py").read_text()
export_code=source[source.index('report = {"status"'):]
exec(compile(export_code,str(ROOT/"build_holders.py"),"exec"),globals())
report["revision"]="Full-width base transitions; cheek mouth is an exact common tangent to the insertion rounds"
report["styling"]={"user_sketch_preserved":user.Name,"contour_sketch_fully_constrained":sk.FullyConstrained,
                   "upper_transition_radius_mm":4,"clamp_top_corner_radius_mm":2,
                   "bottom_corner_radius_mm":1.2,"external_chamfer_mm":.6,
                   "native_final_feature":finish.Name}
report["styling"]["base_transition_depth_mm"]=P.ClampWidth.Value
report["styling"]["mouth_common_tangent"]=True
# Verify the tangent analytically against both actual insertion-round circles.
a=math.radians(P.LaptopAngle.Value)
def local_point(point):
    dy=point.x-P.FrontY.Value
    dz=point.y-P.FrontZ.Value
    return App.Vector(-dy*math.cos(a)+dz*math.sin(a),dy*math.sin(a)+dz*math.cos(a),0)
t1=local_point(doc.UnifiedCheekSketch.Geometry[3].StartPoint)
t2=local_point(doc.UnifiedCheekSketch.Geometry[4].StartPoint)
r=doc.InsertionFillets.Radius.Value
c1=App.Vector(P.UpperGrip.Value-r,evaluated(upper)-r,0)
c2=App.Vector(P.LowerGrip.Value-r,evaluated(lower)+P.RailWall.Value-r,0)
direction=t2-t1
direction.normalize()
errors=[]
for tangent,center in ((t1,c1),(t2,c2)):
    radial=tangent-center
    errors.extend([abs(radial.Length-r),abs(radial.dot(direction))])
if max(errors)>1e-7:
    raise RuntimeError("Mouth tangent verification failed: "+str(errors))
report["styling"]["tangent_max_error_mm"]=max(errors)
(ROOT/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
doc.save()
print("Styled model saved; user's sketch preserved:",user.Name)
