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
points=[(back,top),yz(upper_join,upper),
        yz("Parameters.UpperGrip - 1.2 mm",upper),
        yz("Parameters.UpperGrip",upper+" - 1.2 mm"),
        yz("Parameters.LowerGrip",lower+" + Parameters.RailWall - 1.2 mm"),
        yz("Parameters.LowerGrip - 1.2 mm",lower),
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
report["revision"]="User-sketched unified cheek, diagonal mouth, rounded external transitions and 0.6 mm rim chamfers"
report["styling"]={"user_sketch_preserved":user.Name,"contour_sketch_fully_constrained":sk.FullyConstrained,
                   "upper_transition_radius_mm":4,"clamp_top_corner_radius_mm":2,
                   "bottom_corner_radius_mm":1.2,"external_chamfer_mm":.6,
                   "native_final_feature":finish.Name}
(ROOT/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
doc.save()
print("Styled model saved; user's sketch preserved:",user.Name)
