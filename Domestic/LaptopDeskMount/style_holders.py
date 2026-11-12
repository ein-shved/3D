"""Apply the user's sketched contour and external edge treatment in FreeCAD."""
from pathlib import Path
import json
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher

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
